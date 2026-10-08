from datetime import datetime, timezone
from app.db import get_db
from app.utils.ids import new
from app.services.circular import finance_settings


def now():
    return datetime.now(timezone.utc)


def _participant(user_id, db):
    if not user_id:
        return None
    return db.users.find_one({"_id": user_id}, {"password_hash": 0})


def _split_amount(gross, has_collector, has_contributor):
    f = finance_settings()
    gross = round(max(0.0, float(gross or 0)), 2)
    system_fee = round(gross * float(f.get("system_commission_percent", 0)) / 100, 2)
    distributable = round(max(0.0, gross - system_fee), 2)
    source_pct = float(f.get("source_share_percent", 60.0))
    individual_pct = float(f.get("individual_share_percent", 40.0))
    total_pct = max(0.01, source_pct + individual_pct)

    collector_base = 0.0
    contributor_base = 0.0
    if has_collector and has_contributor:
        collector_base = round(distributable * source_pct / total_pct, 2)
        contributor_base = round(distributable - collector_base, 2)
    elif has_collector:
        collector_base = distributable
    elif has_contributor:
        contributor_base = distributable

    collector_fee = round(collector_base * float(f.get("source_service_fee_percent", 0)) / 100, 2)
    contributor_fee = round(contributor_base * float(f.get("individual_service_fee_percent", 0)) / 100, 2)
    return {
        "gross": gross,
        "system_fee": system_fee,
        "distributable": distributable,
        "collector_gross": collector_base,
        "collector_fee": collector_fee,
        "collector_net": round(max(0, collector_base - collector_fee), 2),
        "contributor_gross": contributor_base,
        "contributor_fee": contributor_fee,
        "contributor_net": round(max(0, contributor_base - contributor_fee), 2),
        "rules_snapshot": f.copy(),
    }


def settle_marketplace_order(order_id, received_by):
    """Release marketplace funds only after the buyer confirms physical receipt.

    Each order line gets its own settlement record. Existing settlement records
    are skipped so a retry can safely resume after a partial failure.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database is not configured.")
    order = db.orders.find_one({"_id": order_id, "buyer_id": received_by})
    if not order:
        raise ValueError("Order not found or not owned by this buyer.")
    if order.get("payment_status") != "paid":
        raise ValueError("The order cannot be marked received until payment is confirmed.")
    if order.get("settlement_status") == "SETTLED":
        return order

    # Lock the workflow state so two browser tabs cannot settle the same order.
    locked = db.orders.find_one_and_update(
        {"_id": order_id, "buyer_id": received_by, "payment_status": "paid", "settlement_status": {"$in": ["AWAITING_RECEIPT", "RETRY_REQUIRED"]}},
        {"$set": {"settlement_status": "PROCESSING", "updated_at": now()}},
        return_document=__import__('pymongo').ReturnDocument.AFTER,
    )
    if not locked:
        return db.orders.find_one({"_id": order_id})
    order = locked

    try:
        totals = {"gross": 0.0, "system_fee": 0.0, "collector_fee": 0.0, "contributor_fee": 0.0,
                  "collector_net": 0.0, "contributor_net": 0.0}
        for index, item in enumerate(order.get("items", [])):
            existing = db.marketplace_settlements.find_one({"order_id": order_id, "item_index": index})
            if existing:
                for key in totals:
                    totals[key] += float(existing.get(key, 0) or 0)
                continue

            collector_id = item.get("collector_id")
            contributor_id = item.get("contributor_id")
            owner = _participant(item.get("seller_id"), db)
            if owner:
                if owner.get("account_type") == "source" and not collector_id:
                    collector_id = owner.get("_id")
                elif owner.get("account_type") == "individual" and not contributor_id:
                    contributor_id = owner.get("_id")

            # A line can still be paid to its seller when no explicit collector
            # or contributor is assigned. This prevents funds from disappearing.
            if not collector_id and not contributor_id and item.get("seller_id"):
                if owner and owner.get("account_type") == "source":
                    collector_id = item.get("seller_id")
                else:
                    contributor_id = item.get("seller_id")

            split = _split_amount(item.get("line_total", 0), bool(collector_id), bool(contributor_id))
            settlement = {
                "_id": new("mset_"), "order_id": order_id, "item_index": index,
                "listing_id": item.get("listing_id"), "material": item.get("material", ""),
                "quantity": item.get("quantity", 0), "buyer_id": order.get("buyer_id"),
                "collector_id": collector_id, "contributor_id": contributor_id,
                "seller_id": item.get("seller_id"), **split,
                "status": "QUEUED", "received_by": received_by, "created_at": now(),
            }
            db.marketplace_settlements.insert_one(settlement)

            payouts = []
            if collector_id and split["collector_net"] > 0:
                payouts.append({"_id": new("pay_"), "order_id": order_id, "settlement_id": settlement["_id"],
                                "beneficiary_id": collector_id, "beneficiary_type": "COLLECTOR",
                                "gross": split["collector_gross"], "fee": split["collector_fee"],
                                "net": split["collector_net"], "status": "QUEUED", "created_at": now()})
            if contributor_id and split["contributor_net"] > 0:
                payouts.append({"_id": new("pay_"), "order_id": order_id, "settlement_id": settlement["_id"],
                                "beneficiary_id": contributor_id, "beneficiary_type": "CONTRIBUTOR",
                                "gross": split["contributor_gross"], "fee": split["contributor_fee"],
                                "net": split["contributor_net"], "status": "QUEUED", "created_at": now()})
            if payouts:
                db.payouts.insert_many(payouts)

            db.platform_revenue.insert_one({
                "_id": new("rev_"), "order_id": order_id, "settlement_id": settlement["_id"],
                "system_commission": split["system_fee"],
                "source_service_fee": split["collector_fee"],
                "individual_service_fee": split["contributor_fee"],
                "total_revenue": round(split["system_fee"] + split["collector_fee"] + split["contributor_fee"], 2),
                "currency": "KES", "created_at": now(),
            })
            for key in totals:
                totals[key] += float(settlement.get({"gross":"gross", "system_fee":"system_fee", "collector_fee":"collector_fee", "contributor_fee":"contributor_fee", "collector_net":"collector_net", "contributor_net":"contributor_net"}[key], 0) or 0)

        db.orders.update_one({"_id": order_id}, {"$set": {
            "status": "received", "settlement_status": "SETTLED", "received_at": now(),
            "received_by": received_by, "settlement_totals": totals, "updated_at": now(),
        }})
        return db.orders.find_one({"_id": order_id})
    except Exception:
        db.orders.update_one({"_id": order_id}, {"$set": {"settlement_status": "RETRY_REQUIRED", "updated_at": now()}})
        raise


def assign_contributor_points(contributor_id, points, actor_id, reason, order_id=None, source="collector"):
    db = get_db()
    if db is None:
        raise RuntimeError("Database is not configured.")
    contributor = db.users.find_one({"_id": contributor_id, "account_type": "individual"})
    if not contributor:
        raise ValueError("Select a registered individual contributor.")
    points = int(points or 0)
    if points <= 0:
        raise ValueError("Points must be greater than zero.")
    reason = (reason or "Verified contribution").strip()[:240]
    ledger = {
        "_id": new("pt_"), "user_id": contributor_id, "type": "EARN",
        "points": points, "description": reason, "assigned_by": actor_id,
        "assignment_source": source, "order_id": order_id, "created_at": now(),
    }
    db.point_ledger.insert_one(ledger)
    db.users.update_one({"_id": contributor_id}, {"$inc": {"points_balance": points, "lifetime_points": points}})
    db.audit_logs.insert_one({"_id": new("aud_"), "action": "CONTRIBUTOR_POINTS_ASSIGNED",
                              "target": contributor_id, "detail": f"{points} points: {reason}",
                              "actor_id": actor_id, "created_at": now()})
    return ledger

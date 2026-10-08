from pymongo import ASCENDING, DESCENDING, GEOSPHERE, MongoClient
from pymongo.errors import OperationFailure

_client = None
_db = None


def _index_signature(info):
    return {
        "key": tuple((k, v) for k, v in info.get("key", {}).items()),
        "unique": bool(info.get("unique", False)),
        "sparse": bool(info.get("sparse", False)),
    }


def _ensure_index(collection, keys, *, name, unique=False, sparse=False):
    """Create/reconcile one index without allowing a legacy option mismatch to
    take the entire application database offline.

    MongoDB identifies an index by its key pattern *and* options. Older CIRCULINK
    deployments already contain some unique indexes, so blindly calling
    create_index() can raise IndexKeySpecsConflict. We inspect the existing index,
    reuse it when compatible, and replace only a conflicting index definition.
    """
    desired = {
        "key": tuple(keys),
        "unique": bool(unique),
        "sparse": bool(sparse),
    }
    existing = list(collection.list_indexes())
    by_name = next((x for x in existing if x.get("name") == name), None)
    if by_name and _index_signature(by_name) == desired:
        return name

    # If the exact key/options already exists under another name, reuse it.
    for info in existing:
        if _index_signature(info) == desired:
            return info.get("name")

    # A same-name legacy index with different options must be replaced.
    if by_name:
        collection.drop_index(name)

    # A same key pattern with incompatible options must be replaced too.
    for info in list(collection.list_indexes()):
        if tuple((k, v) for k, v in info.get("key", {}).items()) == tuple(keys):
            collection.drop_index(info["name"])

    try:
        return collection.create_index(list(keys), name=name, unique=unique, sparse=sparse)
    except OperationFailure as exc:
        # Another warm Vercel invocation may have created the index between the
        # inspection and creation. If the resulting definition is now correct,
        # continue instead of taking the whole request path offline.
        if getattr(exc, "code", None) == 85 or getattr(exc, "code", None) == 86:
            for info in collection.list_indexes():
                if _index_signature(info) == desired:
                    return info.get("name")
        raise


def _ensure_indexes(db):
    specs = {
        "users": [
            ([('email', ASCENDING)], "users_email_unique", True, False),
            ([('account_type', ASCENDING), ('created_at', DESCENDING)], "users_account_type_created", False, False),
            ([('verified', ASCENDING), ('status', ASCENDING)], "users_verified_status", False, False),
        ],
        "otps": [
            ([('email', ASCENDING), ('purpose', ASCENDING), ('created_at', DESCENDING)], "otps_email_purpose_created", False, False),
            ([('expires_at', ASCENDING)], "otps_expires_at", False, False),
        ],
        "listings": [
            ([('status', ASCENDING), ('category', ASCENDING)], "listings_status_category", False, False),
            ([('material', ASCENDING), ('status', ASCENDING)], "listings_material_status", False, False),
            ([('owner_id', ASCENDING), ('created_at', DESCENDING)], "listings_owner_created", False, False),
            ([('location.geo', GEOSPHERE)], "listings_location_geo", False, True),
            ([('status', ASCENDING), ('quantity', ASCENDING)], "listings_status_quantity", False, False),
        ],
        "accounts": [([('user_id', ASCENDING)], "accounts_user", False, False)],
        "demand_posts": [([('status', ASCENDING), ('material', ASCENDING), ('created_at', DESCENDING)], "demand_status_material_created", False, False)],
        "offers": [([('listing_id', ASCENDING), ('buyer_id', ASCENDING), ('status', ASCENDING)], "offers_listing_buyer_status", False, False)],
        "deals": [([('buyer_id', ASCENDING), ('collector_id', ASCENDING), ('status', ASCENDING)], "deals_buyer_collector_status", False, False)],
        "conversations": [([('participants', ASCENDING), ('updated_at', DESCENDING)], "conversations_participants_updated", False, False)],
        "messages": [([('conversation_id', ASCENDING), ('created_at', ASCENDING)], "messages_conversation_created", False, False)],
        "payments": [([('deal_id', ASCENDING), ('status', ASCENDING)], "payments_deal_status", False, False)],
        "escrow": [([('deal_id', ASCENDING), ('status', ASCENDING)], "escrow_deal_status", False, False)],
        "batches": [([('deal_id', ASCENDING), ('status', ASCENDING), ('created_at', DESCENDING)], "batches_deal_status_created", False, False)],
        "certificates": [([('certificate_no', ASCENDING)], "certificates_no_unique", True, False)],
        "notifications": [([('user_id', ASCENDING), ('read', ASCENDING), ('created_at', DESCENDING)], "notifications_user_read_created", False, False)],
        "audit_logs": [([('actor_id', ASCENDING), ('created_at', DESCENDING)], "audit_actor_created", False, False)],
        "material_requests": [([('company_id', ASCENDING), ('status', ASCENDING), ('created_at', DESCENDING)], "material_requests_company_status_created", False, False)],
        "fulfillments": [([('request_id', ASCENDING), ('status', ASCENDING)], "fulfillments_request_status", False, False)],
        "payouts": [([('status', ASCENDING), ('created_at', DESCENDING)], "payouts_status_created", False, False)],
        "point_ledger": [([('user_id', ASCENDING), ('created_at', DESCENDING)], "points_user_created", False, False)],
        "point_redemptions": [([('user_id', ASCENDING), ('status', ASCENDING)], "point_redemptions_user_status", False, False)],
        "contact_messages": [([('created_at', DESCENDING)], "contact_created", False, False)],
        "media": [([('created_at', DESCENDING)], "media_created", False, False), ([('owner_id', ASCENDING), ('created_at', DESCENDING)], "media_owner_created", False, False)],
        "badges": [([('user_id', ASCENDING), ('created_at', DESCENDING)], "badges_user_created", False, False)],
        "mhub_events": [([('created_at', DESCENDING)], "mhub_events_created", False, False)],
        "platform_revenue": [([('created_at', DESCENDING)], "platform_revenue_created", False, False)],
        "transactions": [
            ([('order_id', ASCENDING), ('user_id', ASCENDING), ('created_at', DESCENDING)], "transactions_order_user_created", False, False),
            ([('checkout_request_id', ASCENDING)], "transactions_checkout_request", False, True),
            ([('status', ASCENDING), ('created_at', DESCENDING)], "transactions_status_created", False, False),
        ],
        "mpesa_callbacks": [([('checkout_request_id', ASCENDING), ('created_at', DESCENDING)], "mpesa_callbacks_checkout_created", False, False)],
        "orders": [([('buyer_id', ASCENDING), ('created_at', DESCENDING)], "orders_buyer_created", False, False), ([('status', ASCENDING), ('payment_status', ASCENDING)], "orders_status_payment", False, False)],
        "pickups": [([('user_id', ASCENDING), ('created_at', DESCENDING)], "pickups_user_created", False, False), ([('status', ASCENDING), ('scheduled_at', ASCENDING)], "pickups_status_scheduled", False, False)],
        "events": [([('type', ASCENDING), ('created_at', DESCENDING)], "events_type_created", False, False)],
        "matches": [([('listing_id', ASCENDING), ('buyer_id', ASCENDING), ('created_at', DESCENDING)], "matches_listing_buyer_created", False, False)],
        "plans": [([('status', ASCENDING), ('created_at', DESCENDING)], "plans_status_created", False, False)],
        "subscriptions": [([('user_id', ASCENDING), ('status', ASCENDING)], "subscriptions_user_status", False, False)],
        "settings": [([('key', ASCENDING)], "settings_key_unique", True, False)],
        "platform_layers": [([('layer_type', ASCENDING), ('key', ASCENDING)], "platform_layers_type_key_unique", True, False), ([('enabled', ASCENDING), ('sort_order', ASCENDING)], "platform_layers_enabled_order", False, False)],
        "map_points": [([('layer', ASCENDING), ('status', ASCENDING)], "map_points_layer_status", False, False), ([('location', GEOSPHERE)], "map_points_location", False, True)],
        "content_blocks": [([('page', ASCENDING), ('slot', ASCENDING)], "content_blocks_page_slot_unique", True, False)],
        "feature_flags": [([('key', ASCENDING)], "feature_flags_key_unique", True, False)],
        "workflow_states": [([('workflow', ASCENDING), ('key', ASCENDING)], "workflow_states_workflow_key_unique", True, False)],
        "material_catalog": [([('slug', ASCENDING)], "material_catalog_slug_unique", True, False)],
        "verification_requirements": [([('role', ASCENDING), ('key', ASCENDING)], "verification_role_key_unique", True, False)],
        "notification_preferences": [([('user_id', ASCENDING), ('event', ASCENDING)], "notification_preferences_user_event_unique", True, False)],
        "notification_event_types": [([('key', ASCENDING)], "notification_event_types_key_unique", True, False)],
        "sdg_goals": [([('goal_no', ASCENDING)], "sdg_goals_no_unique", True, False)],
    }
    for collection_name, indexes in specs.items():
        collection = db[collection_name]
        for keys, name, unique, sparse in indexes:
            _ensure_index(collection, keys, name=name, unique=unique, sparse=sparse)


def init_db(app):
    global _client, _db
    uri = (app.config.get("MONGODB_URI") or "").strip()
    if not uri:
        app.logger.warning("MONGODB_URI is not configured; database-backed features are unavailable.")
        _client = None
        _db = None
        return None
    try:
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=int(app.config.get("MONGODB_SERVER_SELECTION_TIMEOUT_MS", 5000)),
            connectTimeoutMS=int(app.config.get("MONGODB_CONNECT_TIMEOUT_MS", 5000)),
            retryWrites=True,
        )
        _client.admin.command("ping")
        _db = _client[app.config.get("MONGODB_DB", "link")]
        _ensure_indexes(_db)
        _bootstrap_platform(_db)
        app.logger.info("MongoDB connected: database=%s", _db.name)
        return _db
    except Exception:
        app.logger.exception("Unable to initialise MongoDB.")
        _db = None
        return None


def _bootstrap_platform(db):
    """Persist configurable product/UI/map/workflow layers represented by the
    Circulink HTML prototype. Markup and CSS remain version-controlled templates;
    data-bearing factors become editable, auditable database records.
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    layers = [
        ("page", "home", {"route": "/", "title": "Turn waste into verified raw material.", "enabled": True, "sort_order": 10}),
        ("page", "marketplace", {"route": "/marketplace/", "title": "Find material near you", "enabled": True, "sort_order": 20}),
        ("page", "collector_workspace", {"route": "/dashboard/", "title": "Your recycling, collected and paid for", "enabled": True, "sort_order": 30}),
        ("page", "buyer_workspace", {"route": "/dashboard/", "title": "Secure steady volume", "enabled": True, "sort_order": 40}),
        ("page", "compliance", {"route": "/circular/requests", "title": "Audit-ready, every batch", "enabled": True, "sort_order": 50}),
        ("page", "wallet", {"route": "/circular/wallet", "title": "Paid when the weight is confirmed", "enabled": True, "sort_order": 60}),
        ("page", "admin", {"route": "/admin/", "title": "Platform health at a glance", "enabled": True, "sort_order": 90}),
        ("navigation", "primary", {"items": [{"label": "Overview", "href": "/"}, {"label": "Marketplace", "href": "/marketplace/"}, {"label": "Demand & requests", "href": "/circular/requests"}, {"label": "How it works", "href": "/about"}, {"label": "Contact", "href": "/contact"}], "enabled": True, "sort_order": 1}),
        ("map_layer", "collectors", {"label": "Collectors / sources", "marker": "green_circle", "enabled": True, "sort_order": 10}),
        ("map_layer", "buyers", {"label": "Verified buyers", "marker": "blue_square", "enabled": True, "sort_order": 20}),
        ("map_layer", "listings", {"label": "Active material listings", "marker": "green_circle", "enabled": True, "sort_order": 30}),
        ("map_layer", "dropoff_points", {"label": "Drop-off points", "marker": "neutral_pin", "enabled": True, "sort_order": 40}),
        ("map_layer", "facilities", {"label": "Factories / recycling facilities", "marker": "blue_square", "enabled": True, "sort_order": 50}),
        ("workspace", "individual", {"label": "I collect waste", "account_type": "individual", "enabled": True, "sort_order": 10}),
        ("workspace", "source", {"label": "I collect waste", "account_type": "source", "enabled": True, "sort_order": 20}),
        ("workspace", "company", {"label": "I buy recycled material", "account_type": "company", "enabled": True, "sort_order": 30}),
        ("workspace", "compliance_reporter", {"label": "I report under EPR", "account_type": "company", "enabled": True, "sort_order": 40}),
        ("workflow", "circular_material", {"steps": ["list", "match", "weigh_and_pay", "record"], "enabled": True, "sort_order": 10}),
        ("workflow", "payment", {"steps": ["request", "provider_confirmation", "record", "receipt"], "enabled": True, "sort_order": 20}),
        ("workflow", "batch", {"steps": ["source", "weigh", "signoff", "compliance_record", "certificate"], "enabled": True, "sort_order": 30}),
        ("feature", "verified_accounts", {"label": "Only checked accounts can trade", "enabled": True, "sort_order": 10}),
        ("feature", "real_listing_photos", {"label": "Real marketplace photos required", "enabled": True, "sort_order": 20}),
        ("feature", "public_certificate_verification", {"label": "Public QR certificate verification", "enabled": True, "sort_order": 30}),
        ("feature", "media_retention", {"label": "Unreferenced media cleanup after 12 hours", "retention_hours": 12, "enabled": True, "sort_order": 40}),
        ("feature", "epr_traceability", {"label": "Batch-level EPR traceability", "enabled": True, "sort_order": 50}),
    ]
    for layer_type, key, payload in layers:
        doc = {"layer_type": layer_type, "key": key, **payload, "updated_at": now}
        db.platform_layers.update_one({"layer_type": layer_type, "key": key}, {"$set": doc, "$setOnInsert": {"created_at": now}}, upsert=True)

    map_points = [
        {"key": "nyeri_campus_collection", "layer": "dropoff_points", "name": "Campus collection point", "type": "dropoff", "location": {"type": "Point", "coordinates": [36.817223, -1.286389]}, "status": "active"},
        {"key": "nairobi_event_collection", "layer": "dropoff_points", "name": "Event collection point", "type": "dropoff", "location": {"type": "Point", "coordinates": [36.821945, -1.292066]}, "status": "active"},
        {"key": "business_collection_point", "layer": "facilities", "name": "Custom business point", "type": "facility", "location": {"type": "Point", "coordinates": [36.812, -1.278]}, "status": "active"},
    ]
    for point in map_points:
        point["updated_at"] = now
        db.map_points.update_one({"key": point["key"]}, {"$set": point, "$setOnInsert": {"created_at": now}}, upsert=True)

    from app.services.catalog import CATEGORIES, MATERIALS
    for value in CATEGORIES:
        db.material_catalog.update_one({"slug": f"category:{value}"}, {"$set": {"slug": f"category:{value}", "kind": "category", "name": value, "enabled": True, "updated_at": now}, "$setOnInsert": {"created_at": now}}, upsert=True)
    for value in MATERIALS:
        db.material_catalog.update_one({"slug": f"material:{value.lower().replace(' ', '-') }"}, {"$set": {"slug": f"material:{value.lower().replace(' ', '-') }", "kind": "material", "name": value, "enabled": True, "updated_at": now}, "$setOnInsert": {"created_at": now}}, upsert=True)

    defaults = [
        ("tax", {"enabled": False, "percent": 0.0, "currency": "KES"}),
        ("marketplace", {"service_fee_percent": 0.0, "pickup_fee": 0.0, "commission_percent": 10.0}),
        ("media_retention", {"unreferenced_hours": 12}),
        ("platform", {"name": "CIRCULINK", "slogan": "TUNA TAKA TAKA", "timezone": "Africa/Nairobi", "currency": "KES"}),
    ]
    for key, value in defaults:
        db.settings.update_one({"key": key}, {"$setOnInsert": {"key": key, "value": value, "created_at": now}, "$set": {"updated_at": now}}, upsert=True)

    content_blocks = [
        ("home", "buying_prices", "Today's buying prices"),
        ("home", "process", "Four steps from collection to compliance record"),
        ("home", "workspaces", "Pick your workspace"),
        ("marketplace", "hero", "Find material near you"),
        ("collector", "hero", "Your recycling, collected and paid for"),
        ("collector", "next_pickup", "Next pickup"),
        ("buyer", "hero", "Secure steady volume"),
        ("buyer", "scorecard", "Supplier scorecard"),
        ("compliance", "hero", "Audit-ready, every batch"),
        ("compliance", "obligation", "Obligation by material"),
        ("wallet", "hero", "Paid when the weight is confirmed"),
        ("admin", "hero", "Platform health at a glance"),
        ("verification", "hero", "Only checked accounts can trade"),
    ]
    for page, slot, title in content_blocks:
        db.content_blocks.update_one(
            {"page": page, "slot": slot},
            {"$set": {"page": page, "slot": slot, "content": {"title": title}, "enabled": True, "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    workflow_states = {
        "listing": ["draft", "active", "reserved", "sold_out", "archived"],
        "order": ["pending", "paid", "cancelled", "fulfilled"],
        "payment": ["pending", "awaiting_callback", "processing", "paid", "failed"],
        "pickup": ["requested", "scheduled", "collected", "weighed", "completed", "cancelled"],
        "batch": ["created", "awaiting_weigh_slip", "complete", "missing", "cancelled"],
        "certificate": ["draft", "VALID", "REVOKED"],
        "verification": ["pending", "under_review", "approved", "declined"],
    }
    for workflow, states in workflow_states.items():
        for order, state in enumerate(states, 1):
            db.workflow_states.update_one(
                {"workflow": workflow, "key": state},
                {"$set": {"workflow": workflow, "key": state, "sort_order": order, "enabled": True, "updated_at": now}, "$setOnInsert": {"created_at": now}},
                upsert=True,
            )

    verification = {
        "individual": [("email", "Verified email", True), ("phone", "Kenyan phone", True)],
        "source": [("email", "Verified email", True), ("phone", "Kenyan phone", True), ("identity", "Identity review", True), ("payout", "M-Pesa payout details", True)],
        "company": [("email", "Verified email", True), ("company_registration", "Company registration", True), ("nema_licence", "NEMA licence where applicable", True), ("contact", "Authorised contact", True)],
    }
    for role, requirements in verification.items():
        for key, label, required in requirements:
            db.verification_requirements.update_one(
                {"role": role, "key": key},
                {"$set": {"role": role, "key": key, "label": label, "required": required, "updated_at": now}, "$setOnInsert": {"created_at": now}},
                upsert=True,
            )

    notification_events = [
        ("security", "Security alerts", "locked"),
        ("payment", "Payment updates", "locked"),
        ("legal", "Legal and compliance alerts", "locked"),
        ("listing", "Listing activity", "configurable"),
        ("offer", "Offers and negotiations", "configurable"),
        ("pickup", "Pickup updates", "configurable"),
        ("message", "Messages", "configurable"),
        ("compliance", "Compliance progress", "configurable"),
    ]
    for key, label, policy in notification_events:
        db.notification_event_types.update_one(
            {"key": key},
            {"$set": {"key": key, "label": label, "policy": policy, "enabled": True, "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    sdgs = [
        (1, "No Poverty"), (8, "Decent Work and Economic Growth"), (9, "Industry, Innovation and Infrastructure"),
        (11, "Sustainable Cities and Communities"), (12, "Responsible Consumption and Production"),
        (13, "Climate Action"), (14, "Life Below Water"), (15, "Life on Land"), (17, "Partnerships for the Goals"),
    ]
    for goal_no, title in sdgs:
        db.sdg_goals.update_one({"goal_no": goal_no}, {"$set": {"goal_no": goal_no, "title": title, "enabled": True, "updated_at": now}, "$setOnInsert": {"created_at": now}}, upsert=True)

    flags = ["marketplace", "map", "otp_verification", "mpesa", "receipts", "certificates", "epr_traceability", "notifications", "media_retention", "admin_audit"]
    for key in flags:
        db.feature_flags.update_one({"key": key}, {"$setOnInsert": {"key": key, "enabled": True, "created_at": now}, "$set": {"updated_at": now}}, upsert=True)


def get_db():
    """Return the configured Mongo database or None."""
    return _db


def db_configured():
    return _db is not None

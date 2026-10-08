import os
import bcrypt
from datetime import datetime, timezone
from app.db import get_db
from app.utils.ids import new


def create(d):
    db = get_db()
    if db is None:
        raise RuntimeError("Database is not configured.")
    email = d["email"].lower().strip()
    u = {
        "_id": new("usr_"),
        "name": d["name"].strip(),
        "email": email,
        "phone": d.get("phone", ""),
        "password_hash": bcrypt.hashpw(d["password"].encode(), bcrypt.gensalt()).decode(),
        "role": "ADMIN" if email == os.getenv("ADMIN_EMAIL", "circulink1@gmail.com").lower() else "USER",
        "account_type": d.get("account_type", "individual"),
        "verified": False,
        "status": "active",
        "verification_status": "pending",
        "points_balance": 0,
        "lifetime_points": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    db.users.insert_one(u)
    db.accounts.update_one(
        {"user_id": u["_id"]},
        {"$set": {"user_id": u["_id"], "account_type": u["account_type"], "email": u["email"], "status": "active", "updated_at": datetime.now(timezone.utc)}, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    db.events.insert_one({"_id": new("evt_"), "type": "ACCOUNT_CREATED", "user_id": u["_id"], "account_type": u["account_type"], "created_at": datetime.now(timezone.utc)})
    db.audit_logs.insert_one({"_id": new("aud_"), "actor_id": u["_id"], "action": "ACCOUNT_CREATED", "target": u["_id"], "detail": "Self-service registration", "created_at": datetime.now(timezone.utc)})
    return u


def by_email(e):
    db = get_db()
    return db.users.find_one({"email": e.lower().strip()}) if db is not None else None


def check(u, p):
    return bool(u and bcrypt.checkpw(p.encode(), u["password_hash"].encode()))

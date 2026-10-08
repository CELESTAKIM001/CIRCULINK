from app.db import get_db


def enabled_layers(layer_type=None):
    db = get_db()
    if db is None:
        return []
    query = {"enabled": True}
    if layer_type:
        query["layer_type"] = layer_type
    return list(db.platform_layers.find(query, {"_id": 0}).sort("sort_order", 1))


def layer(layer_type, key):
    db = get_db()
    if db is None:
        return None
    return db.platform_layers.find_one({"layer_type": layer_type, "key": key})

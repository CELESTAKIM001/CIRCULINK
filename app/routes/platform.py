from datetime import datetime, timezone
from flask import Blueprint, render_template, request, current_app
from app.db import get_db
from app.utils.auth import required, user

platform_bp = Blueprint('platform', __name__, url_prefix='/platform')


def _count(db, collection, query=None):
    if db is None:
        return 0
    try:
        return db[collection].count_documents(query or {})
    except Exception:
        return 0


def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sum_field(rows, *keys):
    total = 0.0
    for row in rows:
        for key in keys:
            value = row.get(key)
            number = _number(value, None)
            if number is not None:
                total += number
                break
    return total


def _safe_find(db, collection, query=None, sort=None, limit=50, projection=None):
    """Read platform data defensively so one optional collection/record cannot 500 the workspace."""
    try:
        cur = db[collection].find(query or {}, projection)
        if sort:
            cur = cur.sort(*sort)
        return list(cur.limit(limit))
    except Exception:
        current_app.logger.exception("Platform read failed: %s", collection)
        return []


def _plain_map_points(rows):
    out = []
    for row in rows:
        try:
            loc = row.get('location') or {}
            coords = loc.get('coordinates') if isinstance(loc, dict) else None
            if not isinstance(coords, (list, tuple)) or len(coords) < 2:
                continue
            lng, lat = float(coords[0]), float(coords[1])
            if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                continue
            out.append({
                'name': str(row.get('name') or 'CIRCULINK point'),
                'type': str(row.get('type') or 'facility'),
                'layer': str(row.get('layer') or ''),
                'location': {'coordinates': [lng, lat]},
            })
        except (TypeError, ValueError):
            continue
    return out


def _platform_data(u):
    db = get_db()
    if db is None:
        return {
            'db_ready': False, 'listings': [], 'demands': [], 'orders': [], 'transactions': [],
            'batches': [], 'notifications': [], 'conversations': [], 'map_points': [],
            'stats': {}, 'verification': {}, 'materials': [], 'admin': {}, 'compliance': {},
        }

    uid = u['_id']
    is_admin = u.get('role') == 'ADMIN'
    account_type = u.get('account_type', 'individual')

    listings = _safe_find(db, 'listings', {'status': {'$in': ['active', 'reserved', 'sold_out']}}, ('created_at', -1), 100)
    demands = _safe_find(db, 'material_requests', {'status': {'$in': ['OPEN', 'open', 'ACTIVE', 'active']}}, ('created_at', -1), 50)
    orders = _safe_find(db, 'orders', {'buyer_id': uid}, ('created_at', -1), 30)
    transactions = _safe_find(db, 'transactions', {'user_id': uid}, ('created_at', -1), 30)
    batches = _safe_find(db, 'batches', {'$or': [{'buyer_id': uid}, {'owner_id': uid}, {'collector_id': uid}]}, ('created_at', -1), 50)
    notifications = _safe_find(db, 'notifications', {'user_id': uid}, ('created_at', -1), 20)
    conversations = _safe_find(db, 'conversations', {'participants': uid}, ('updated_at', -1), 20)
    map_points = _plain_map_points(_safe_find(db, 'map_points', {'status': 'active'}, None, 300, {'_id': 0, 'name': 1, 'type': 1, 'layer': 1, 'location': 1}))

    for item in listings:
        try:
            loc = item.get('location') or {}
            lat, lng = loc.get('lat'), loc.get('lng')
            if lat is not None and lng is not None:
                map_points.append({
                    'name': str(item.get('title') or 'Material listing'),
                    'type': 'listing',
                    'layer': 'listings',
                    'location': {'coordinates': [float(lng), float(lat)]},
                })
        except (TypeError, ValueError):
            continue

    listing_kg = _sum_field(listings, 'quantity')
    traded_kg = _sum_field(batches, 'weight', 'kg', 'quantity')
    unread = _count(db, 'notifications', {'user_id': uid, 'read': {'$ne': True}})
    paid_total = sum(_number(x.get('amount', 0)) for x in transactions if str(x.get('status', '')).lower() in {'paid', 'success', 'completed'})

    epr = db.settings.find_one({'key': 'epr_target'}) or {}
    epr_value = (epr.get('value') or {}) if isinstance(epr.get('value'), dict) else {}
    target_kg = _number(epr_value.get('target_kg'), None)
    progress = None
    if target_kg is not None and target_kg > 0:
        progress = min(100.0, traded_kg / target_kg * 100.0)

    verification = {
        'email': bool(u.get('verified')),
        'status': u.get('verification_status', 'pending'),
        'account_type': account_type,
        'company_registration': bool(u.get('company_registration') or u.get('company_reg_no')),
        'nema_licence': bool(u.get('nema_licence') or u.get('nema_license')),
        'phone': bool(u.get('phone')),
        'payout': bool(u.get('mpesa_number') or u.get('payout_phone')),
    }

    admin = {}
    if is_admin:
        admin = {
            'users': _count(db, 'users'),
            'pending_verification': _count(db, 'users', {'verification_status': {'$in': ['pending', 'under_review']}}),
            'active_listings': _count(db, 'listings', {'status': 'active'}),
            'open_demands': _count(db, 'material_requests', {'status': {'$in': ['OPEN', 'open', 'ACTIVE', 'active']}}),
            'open_disputes': _count(db, 'payments', {'status': {'$in': ['disputed', 'DISPUTED']}}),
            'audit_events': _count(db, 'audit_logs'),
        }

    # Only approved material types appear in user-facing dropdowns.
    materials = _safe_find(db, 'material_catalog', {
        'kind': 'material', 'enabled': True,
        '$or': [{'status': 'approved'}, {'status': {'$exists': False}}],
    }, ('name', 1), 100, {'_id': 0, 'name': 1, 'slug': 1, 'category': 1})
    if not materials:
        materials = [{'name': x} for x in ['Bottle tops', 'Paper offcuts', 'Reusable bricks', 'Laptops', 'Broken machines', 'Machine parts', 'Textile offcuts', 'Cables and boards']]

    return {
        'db_ready': True,
        'listings': listings,
        'demands': demands,
        'orders': orders,
        'transactions': transactions,
        'batches': batches,
        'notifications': notifications,
        'conversations': conversations,
        'map_points': map_points,
        'materials': materials,
        'verification': verification,
        'admin': admin,
        'compliance': {'target_kg': target_kg, 'traded_kg': traded_kg, 'progress': progress},
        'stats': {
            'active_listings': _count(db, 'listings', {'status': 'active'}),
            'available_kg': listing_kg,
            'traded_kg': traded_kg,
            'unread': unread,
            'paid_total': paid_total,
            'certificates': _count(db, 'certificates', {'owner_id': uid, 'status': 'VALID'}),
            'orders': len(orders),
        },
    }


@platform_bp.get('/')
@required
def workspace():
    u = user()
    view = request.args.get('view', 'home')
    allowed = {'home', 'household', 'marketplace', 'collector', 'buyer', 'compliance', 'transactions', 'messages', 'verification', 'admin', 'system'}
    if view not in allowed:
        view = 'home'
    if view == 'admin' and u.get('role') != 'ADMIN':
        view = 'home'
    return render_template('platform/workspace.html', user=u, active_view=view, **_platform_data(u))

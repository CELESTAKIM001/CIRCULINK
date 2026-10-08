import json
from flask import Blueprint, render_template, request, redirect, flash, current_app
from app.utils.auth import required, user
from app.repositories.listings import find, one, add
from app.repositories.orders import create
from app.services.media import upload
from app.utils.ids import new
from datetime import datetime, timezone
import re

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")


def _slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:70]


@marketplace_bp.route("/material-types/new", methods=["GET", "POST"])
@required
def material_type_request():
    db = __import__("app.db", fromlist=["get_db"]).get_db()
    if db is None:
        flash("The material catalog is unavailable right now.", "error")
        return redirect("/marketplace/add")
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip().lower()
        description = request.form.get("description", "").strip()
        if len(name) < 2 or len(name) > 80:
            flash("Enter a material type between 2 and 80 characters.", "error")
            return render_template("marketplace/material_type_request.html", categories=_catalog_categories(db), form=request.form)
        slug = _slug(name)
        existing = db.material_catalog.find_one({"kind": "material", "$or": [{"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}, {"slug": {"$regex": f"^{re.escape(slug)}$", "$options": "i"}}]})
        if existing and existing.get("status") == "approved":
            flash("That material type is already available in the marketplace.", "error")
            return redirect("/marketplace/add")
        if existing and existing.get("status") == "pending":
            flash("That material type is already awaiting admin approval.", "info")
            return redirect("/marketplace/add")
        doc = {"_id": new("mtr_"), "slug": f"request:{new('slug_')}", "kind": "material", "name": name, "category": category or "other", "description": description, "status": "pending", "enabled": False, "requested_by": user()["_id"], "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}
        db.material_catalog.insert_one(doc)
        flash("Material type submitted. It will appear in the listing dropdown after admin approval.", "success")
        return redirect("/marketplace/add")
    return render_template("marketplace/material_type_request.html", categories=_catalog_categories(db), form={})


def _catalog_categories(db):
    try:
        rows = list(db.material_catalog.find({"kind": "category", "enabled": True}, {"_id": 0, "name": 1}).sort("name", 1).limit(50))
        return [r.get("name") for r in rows if r.get("name")] or ["plastic", "paper", "construction", "electronics", "textile", "machinery", "other"]
    except Exception:
        current_app.logger.exception("Unable to load catalog categories")
        return ["plastic", "paper", "construction", "electronics", "textile", "machinery", "other"]

@marketplace_bp.get("/")
def index():
    return render_template("marketplace/index.html", listings=find(request.args.get("q", ""), request.args.get("category", "")))

@marketplace_bp.get("/listing/<id>")
def listing(id):
    item = one(id)
    if not item:
        return render_template("error.html", code=404, title="Material not found", message="This marketplace listing is no longer available or has been removed.", retry_url="/marketplace/", retry_label="Return to marketplace"), 404
    return render_template("marketplace/listing.html", item=item)

@marketplace_bp.route("/add", methods=["GET", "POST"])
@required
def add_page():
    if request.method == "POST":
        try:
            files = [f for f in request.files.getlist("images") if f and f.filename]
            if not files:
                raise ValueError("At least one real listing photo is required.")
            images = [upload(f) for f in files[:5]]
            add(request.form, user()["_id"], images)
            flash("Material published with real marketplace photos.", "success")
            return redirect("/marketplace/")
        except Exception as exc:
            flash(str(exc) or "The listing could not be published.", "error")
    db = __import__("app.db", fromlist=["get_db"]).get_db()
    materials = []
    categories = _catalog_categories(db) if db is not None else ["plastic", "paper", "construction", "electronics", "textile", "machinery", "other"]
    if db is not None:
        try:
            materials = list(db.material_catalog.find({"kind":"material", "enabled":True, "$or":[{"status":"approved"},{"status":{"$exists":False}}]}, {"_id":0,"name":1,"category":1}).sort("name",1).limit(100))
        except Exception:
            current_app.logger.exception("Unable to load approved material catalog")
    return render_template("marketplace/add.html", materials=materials, categories=categories)

@marketplace_bp.post("/checkout")
@required
def checkout():
    try:
        items = json.loads(request.form.get("items", "[]"))
        if not isinstance(items, list) or not items:
            raise ValueError("Your cart is empty. Add a material before checking out.")
        total = sum(float(i.get("line_total", 0)) for i in items)
        if total <= 0:
            raise ValueError("The checkout total must be greater than zero.")
        o = create(user()["_id"], items, total)
        return redirect("/pay/" + o["_id"])
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        flash(str(exc) or "We could not create the checkout.", "error")
        return redirect("/marketplace/")
    except Exception:
        from flask import current_app
        current_app.logger.exception("Checkout creation failed")
        flash("We could not create your checkout right now. Your cart was not charged.", "error")
        return redirect("/marketplace/")

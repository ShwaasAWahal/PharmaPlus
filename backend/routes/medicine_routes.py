import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from database.db import db
from models.medicine import Medicine
from models.supplier import Supplier
from models.branch import Branch
from utils.jwt_utils import role_required

logger = logging.getLogger(__name__)
medicine_bp = Blueprint("medicine", __name__, url_prefix="/api/medicines")


# ── Medicines CRUD ─────────────────────────────────────────────────────────────

@medicine_bp.get("")
@jwt_required()
def list_medicines():
    """List all medicines with search and pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    supplier_id = request.args.get("supplier_id", type=int)

    query = Medicine.query.filter_by(is_active=True)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Medicine.name.ilike(like),
                Medicine.generic_name.ilike(like),
                Medicine.barcode.ilike(like),
                Medicine.brand.ilike(like),
            )
        )
    if category:
        query = query.filter(Medicine.category.ilike(f"%{category}%"))
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)

    pagination = query.order_by(Medicine.name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "success": True,
        "medicines": [m.to_dict() for m in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
        "per_page": per_page,
    }), 200


@medicine_bp.get("/<int:medicine_id>")
@jwt_required()
def get_medicine(medicine_id):
    med = Medicine.query.get_or_404(medicine_id)
    include_inv = request.args.get("include_inventory", "false").lower() == "true"
    return jsonify({"success": True, "medicine": med.to_dict(include_inventory=include_inv)}), 200


@medicine_bp.post("")
@jwt_required()
@role_required("admin", "pharmacist")
def add_medicine():
    data = request.get_json(silent=True) or {}
    required = ["name", "purchase_price", "selling_price"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing)}"}), 400

    if data.get("barcode") and Medicine.query.filter_by(barcode=data["barcode"]).first():
        return jsonify({"success": False, "message": "Barcode already exists."}), 409

    if data.get("supplier_id") and not Supplier.query.get(data["supplier_id"]):
        return jsonify({"success": False, "message": "Supplier not found."}), 404

    med = Medicine(
        name=data["name"].strip(),
        generic_name=data.get("generic_name", "").strip() or None,
        brand=data.get("brand"),
        category=data.get("category"),
        form=data.get("form"),
        strength=data.get("strength"),
        unit=data.get("unit", "strip"),
        barcode=data.get("barcode"),
        description=data.get("description"),
        requires_prescription=bool(data.get("requires_prescription", False)),
        hsn_code=data.get("hsn_code"),
        tax_percent=float(data.get("tax_percent", 0)),
        purchase_price=float(data["purchase_price"]),
        selling_price=float(data["selling_price"]),
        mrp=float(data["mrp"]) if data.get("mrp") else None,
        supplier_id=data.get("supplier_id"),
    )
    db.session.add(med)
    db.session.commit()
    return jsonify({"success": True, "message": "Medicine added.", "medicine": med.to_dict()}), 201


@medicine_bp.put("/<int:medicine_id>")
@jwt_required()
@role_required("admin", "pharmacist")
def update_medicine(medicine_id):
    med = Medicine.query.get_or_404(medicine_id)
    data = request.get_json(silent=True) or {}

    updatable = [
        "name", "generic_name", "brand", "category", "form", "strength", "unit",
        "description", "requires_prescription", "hsn_code", "tax_percent",
        "purchase_price", "selling_price", "mrp", "supplier_id", "is_active",
    ]
    for field in updatable:
        if field in data:
            setattr(med, field, data[field])

    if "barcode" in data:
        existing = Medicine.query.filter_by(barcode=data["barcode"]).first()
        if existing and existing.id != medicine_id:
            return jsonify({"success": False, "message": "Barcode already in use."}), 409
        med.barcode = data["barcode"]

    db.session.commit()
    return jsonify({"success": True, "medicine": med.to_dict()}), 200


@medicine_bp.delete("/<int:medicine_id>")
@jwt_required()
@role_required("admin")
def delete_medicine(medicine_id):
    med = Medicine.query.get_or_404(medicine_id)
    med.is_active = False
    db.session.commit()
    return jsonify({"success": True, "message": "Medicine deactivated."}), 200


# ── Barcode / QR scan ──────────────────────────────────────────────────────────

@medicine_bp.post("/barcode/scan")
@jwt_required()
def scan_barcode():
    """
    POST /api/medicines/barcode/scan
    Accepts a scanned barcode string and returns medicine information.
    """
    data = request.get_json(silent=True) or {}
    barcode = (data.get("barcode") or "").strip()
    if not barcode:
        return jsonify({"success": False, "message": "barcode field is required."}), 400

    med = Medicine.query.filter_by(barcode=barcode, is_active=True).first()
    if not med:
        return jsonify({"success": False, "message": "No medicine found for this barcode."}), 404

    branch_id = data.get("branch_id")
    result = med.to_dict(include_inventory=False)

    if branch_id:
        from models.inventory import Inventory
        inv_items = Inventory.query.filter_by(
            medicine_id=med.id, branch_id=branch_id, is_active=True
        ).all()
        result["inventory"] = [i.to_dict() for i in inv_items]
        result["total_quantity"] = sum(i.quantity for i in inv_items)

    return jsonify({"success": True, "medicine": result}), 200


# ── Suppliers ──────────────────────────────────────────────────────────────────

@medicine_bp.get("/suppliers")
@jwt_required()
def list_suppliers():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    query = Supplier.query.filter_by(is_active=True)
    pagination = query.order_by(Supplier.name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "success": True,
        "suppliers": [s.to_dict() for s in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


@medicine_bp.post("/suppliers")
@jwt_required()
@role_required("admin")
def add_supplier():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "message": "Supplier name is required."}), 400

    supplier = Supplier(**{k: data[k] for k in (
        "name", "contact_person", "phone", "email", "address",
        "gstin", "license_number", "payment_terms",
    ) if k in data})
    db.session.add(supplier)
    db.session.commit()
    return jsonify({"success": True, "supplier": supplier.to_dict()}), 201


@medicine_bp.put("/suppliers/<int:supplier_id>")
@jwt_required()
@role_required("admin")
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json(silent=True) or {}
    for field in ("name", "contact_person", "phone", "email", "address",
                  "gstin", "license_number", "payment_terms", "rating", "is_active"):
        if field in data:
            setattr(supplier, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "supplier": supplier.to_dict()}), 200


# ── Branches ───────────────────────────────────────────────────────────────────

@medicine_bp.get("/branches")
@jwt_required()
def list_branches():
    branches = Branch.query.filter_by(is_active=True).order_by(Branch.name).all()
    return jsonify({"success": True, "branches": [b.to_dict() for b in branches]}), 200


@medicine_bp.post("/branches")
@jwt_required()
@role_required("admin")
def add_branch():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "message": "Branch name is required."}), 400

    branch = Branch(**{k: data[k] for k in (
        "name", "address", "phone", "email", "license_number", "manager_name"
    ) if k in data})
    db.session.add(branch)
    db.session.commit()
    return jsonify({"success": True, "branch": branch.to_dict()}), 201


@medicine_bp.put("/branches/<int:branch_id>")
@jwt_required()
@role_required("admin")
def update_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    data = request.get_json(silent=True) or {}
    for field in ("name", "address", "phone", "email", "license_number", "manager_name", "is_active"):
        if field in data:
            setattr(branch, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "branch": branch.to_dict()}), 200

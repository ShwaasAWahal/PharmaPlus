import logging
from datetime import date

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from database.db import db
from models.inventory import Inventory
from services import inventory_service
from utils.jwt_utils import role_required

logger = logging.getLogger(__name__)
inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


@inventory_bp.get("")
@jwt_required()
def list_inventory():
    """Paginated inventory list with filters."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    branch_id = request.args.get("branch_id", type=int)
    medicine_id = request.args.get("medicine_id", type=int)
    include_expired = request.args.get("include_expired", "true").lower() == "true"
    low_stock_only = request.args.get("low_stock_only", "false").lower() == "true"

    result = inventory_service.get_inventory(
        branch_id=branch_id,
        medicine_id=medicine_id,
        page=page,
        per_page=per_page,
        include_expired=include_expired,
        include_low_stock_only=low_stock_only,
    )
    return jsonify({"success": True, **result}), 200


@inventory_bp.get("/<int:inventory_id>")
@jwt_required()
def get_inventory_item(inventory_id):
    item = Inventory.query.get_or_404(inventory_id)
    return jsonify({"success": True, "inventory": item.to_dict()}), 200


@inventory_bp.post("")
@jwt_required()
@role_required("admin", "pharmacist")
def add_inventory():
    """Add or restock an inventory batch."""
    data = request.get_json(silent=True) or {}
    required = ["medicine_id", "branch_id", "batch_number", "quantity"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing)}"}), 400

    if int(data["quantity"]) < 0:
        return jsonify({"success": False, "message": "Quantity cannot be negative."}), 400

    # Parse expiry date string if needed
    expiry_date = data.get("expiry_date")
    if expiry_date and isinstance(expiry_date, str):
        try:
            data["expiry_date"] = date.fromisoformat(expiry_date)
        except ValueError:
            return jsonify({"success": False, "message": "Invalid expiry_date format (YYYY-MM-DD)."}), 400

    manufacture_date = data.get("manufacture_date")
    if manufacture_date and isinstance(manufacture_date, str):
        try:
            data["manufacture_date"] = date.fromisoformat(manufacture_date)
        except ValueError:
            return jsonify({"success": False, "message": "Invalid manufacture_date format (YYYY-MM-DD)."}), 400

    item = inventory_service.add_inventory(data)
    return jsonify({"success": True, "message": "Inventory updated.", "inventory": item.to_dict()}), 201


@inventory_bp.put("/<int:inventory_id>")
@jwt_required()
@role_required("admin", "pharmacist")
def update_inventory(inventory_id):
    item = Inventory.query.get_or_404(inventory_id)
    data = request.get_json(silent=True) or {}

    updatable = ["quantity", "low_stock_threshold", "location", "notes", "is_active",
                 "purchase_price", "selling_price"]
    for field in updatable:
        if field in data:
            setattr(item, field, data[field])

    for date_field in ("expiry_date", "manufacture_date"):
        if date_field in data and isinstance(data[date_field], str):
            try:
                setattr(item, date_field, date.fromisoformat(data[date_field]))
            except ValueError:
                return jsonify({"success": False, "message": f"Invalid {date_field} format."}), 400

    db.session.commit()
    return jsonify({"success": True, "inventory": item.to_dict()}), 200


@inventory_bp.delete("/<int:inventory_id>")
@jwt_required()
@role_required("admin")
def delete_inventory(inventory_id):
    item = Inventory.query.get_or_404(inventory_id)
    item.is_active = False
    db.session.commit()
    return jsonify({"success": True, "message": "Inventory record deactivated."}), 200


@inventory_bp.post("/<int:inventory_id>/adjust")
@jwt_required()
@role_required("admin", "pharmacist")
def adjust_stock(inventory_id):
    """Manually adjust stock quantity (positive or negative delta)."""
    data = request.get_json(silent=True) or {}
    delta = data.get("delta")
    if delta is None:
        return jsonify({"success": False, "message": "delta field is required."}), 400

    try:
        item = inventory_service.adjust_stock(
            inventory_id=inventory_id,
            delta=int(delta),
            reason=data.get("reason", "manual adjustment"),
        )
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    return jsonify({"success": True, "inventory": item.to_dict()}), 200


@inventory_bp.get("/alerts/expiring")
@jwt_required()
def expiring_soon():
    """Get medicines expiring within N days (default 30)."""
    days = request.args.get("days", 30, type=int)
    branch_id = request.args.get("branch_id", type=int)
    items = inventory_service.get_expiring_soon(days=days, branch_id=branch_id)
    return jsonify({
        "success": True,
        "count": len(items),
        "items": [i.to_dict() for i in items],
    }), 200


@inventory_bp.get("/alerts/low-stock")
@jwt_required()
def low_stock():
    """Get medicines below their low-stock threshold."""
    branch_id = request.args.get("branch_id", type=int)
    items = inventory_service.get_low_stock(branch_id=branch_id)
    return jsonify({
        "success": True,
        "count": len(items),
        "items": [i.to_dict() for i in items],
    }), 200


@inventory_bp.get("/alerts/expired")
@jwt_required()
def expired_stock():
    """Get all expired inventory still in stock."""
    branch_id = request.args.get("branch_id", type=int)
    items = inventory_service.get_expired_stock(branch_id=branch_id)
    return jsonify({
        "success": True,
        "count": len(items),
        "items": [i.to_dict() for i in items],
    }), 200

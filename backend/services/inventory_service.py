import logging
from datetime import date, timedelta

from database.db import db
from models.inventory import Inventory
from models.medicine import Medicine

logger = logging.getLogger(__name__)


def get_inventory(branch_id=None, medicine_id=None, page=1, per_page=20,
                  include_expired=True, include_low_stock_only=False):
    """Return paginated inventory items with optional filters."""
    query = Inventory.query.filter_by(is_active=True)

    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if medicine_id:
        query = query.filter_by(medicine_id=medicine_id)
    if not include_expired:
        query = query.filter(
            (Inventory.expiry_date == None) | (Inventory.expiry_date >= date.today())
        )
    if include_low_stock_only:
        query = query.filter(Inventory.quantity <= Inventory.low_stock_threshold)

    pagination = query.order_by(Inventory.expiry_date.asc().nullslast()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return {
        "items": [i.to_dict() for i in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
        "per_page": per_page,
    }


def add_inventory(data: dict) -> Inventory:
    """Create or update an inventory record (upsert by batch)."""
    existing = Inventory.query.filter_by(
        medicine_id=data["medicine_id"],
        branch_id=data["branch_id"],
        batch_number=data["batch_number"],
    ).first()

    if existing:
        existing.quantity += data.get("quantity", 0)
        existing.expiry_date = data.get("expiry_date", existing.expiry_date)
        existing.purchase_price = data.get("purchase_price", existing.purchase_price)
        existing.selling_price = data.get("selling_price", existing.selling_price)
        db.session.commit()
        return existing

    item = Inventory(
        medicine_id=data["medicine_id"],
        branch_id=data["branch_id"],
        batch_number=data["batch_number"],
        quantity=data.get("quantity", 0),
        low_stock_threshold=data.get("low_stock_threshold", 10),
        expiry_date=data.get("expiry_date"),
        manufacture_date=data.get("manufacture_date"),
        purchase_price=data.get("purchase_price"),
        selling_price=data.get("selling_price"),
        location=data.get("location"),
        notes=data.get("notes"),
    )
    db.session.add(item)
    db.session.commit()
    return item


def adjust_stock(inventory_id: int, delta: int, reason: str = "adjustment") -> Inventory:
    """Increase or decrease stock quantity."""
    item = Inventory.query.get_or_404(inventory_id)
    if item.quantity + delta < 0:
        raise ValueError("Insufficient stock — cannot reduce below 0.")
    item.quantity += delta
    db.session.commit()
    logger.info(f"Stock adjusted: inventory_id={inventory_id} delta={delta} reason={reason}")
    return item


def get_expiring_soon(days: int = 30, branch_id=None):
    """Return inventory items expiring within `days` days."""
    cutoff = date.today() + timedelta(days=days)
    query = Inventory.query.filter(
        Inventory.is_active == True,
        Inventory.expiry_date != None,
        Inventory.expiry_date <= cutoff,
        Inventory.expiry_date >= date.today(),
        Inventory.quantity > 0,
    )
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    return query.order_by(Inventory.expiry_date.asc()).all()


def get_low_stock(branch_id=None):
    """Return inventory items at or below their low-stock threshold."""
    query = Inventory.query.filter(
        Inventory.is_active == True,
        Inventory.quantity <= Inventory.low_stock_threshold,
    )
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    return query.order_by(Inventory.quantity.asc()).all()


def get_expired_stock(branch_id=None):
    """Return all expired inventory items still in stock."""
    query = Inventory.query.filter(
        Inventory.is_active == True,
        Inventory.expiry_date != None,
        Inventory.expiry_date < date.today(),
        Inventory.quantity > 0,
    )
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    return query.order_by(Inventory.expiry_date.asc()).all()

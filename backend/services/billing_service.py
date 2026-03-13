import logging
from datetime import datetime, timezone

from database.db import db
from models.sales import Sale, SaleItem
from models.inventory import Inventory

logger = logging.getLogger(__name__)


def _generate_invoice_number(branch_id: int) -> str:
    """Generate a unique invoice number."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    count = Sale.query.filter_by(branch_id=branch_id).count() + 1
    return f"INV-{branch_id:03d}-{ts}-{count:04d}"


def create_bill(data: dict, user_id: int) -> Sale:
    """
    Create a sale and deduct inventory.

    data = {
        branch_id, customer_name?, customer_phone?, customer_age?,
        prescription_id?, discount_percent?, payment_method?, amount_paid?, notes?,
        items: [{ medicine_id, inventory_id?, quantity, unit_price, discount_percent?, tax_percent? }]
    }
    """
    branch_id = data["branch_id"]
    items_data = data.get("items", [])
    if not items_data:
        raise ValueError("A bill must contain at least one item.")

    subtotal = 0.0
    tax_total = 0.0
    sale_items = []

    for item_d in items_data:
        qty = int(item_d["quantity"])
        unit_price = float(item_d["unit_price"])
        disc = float(item_d.get("discount_percent", 0))
        tax = float(item_d.get("tax_percent", 0))

        # Deduct inventory if inventory_id provided
        inv = None
        batch_number = item_d.get("batch_number")
        if item_d.get("inventory_id"):
            inv = Inventory.query.get(item_d["inventory_id"])
            if not inv:
                raise ValueError(f"Inventory record {item_d['inventory_id']} not found.")
            if inv.quantity < qty:
                raise ValueError(
                    f"Insufficient stock for medicine_id={item_d['medicine_id']}. "
                    f"Available: {inv.quantity}, Requested: {qty}"
                )
            batch_number = inv.batch_number
            inv.quantity -= qty

        discounted = unit_price * qty * (1 - disc / 100)
        tax_amount = discounted * tax / 100
        line_total = round(discounted + tax_amount, 2)

        subtotal += discounted
        tax_total += tax_amount

        sale_items.append(SaleItem(
            medicine_id=item_d["medicine_id"],
            inventory_id=item_d.get("inventory_id"),
            batch_number=batch_number,
            quantity=qty,
            unit_price=unit_price,
            discount_percent=disc,
            tax_percent=tax,
            line_total=line_total,
        ))

    disc_pct = float(data.get("discount_percent", 0))
    discount_amount = round(subtotal * disc_pct / 100, 2)
    total = round(subtotal - discount_amount + tax_total, 2)
    amount_paid = float(data.get("amount_paid", total))
    change_given = round(amount_paid - total, 2)

    sale = Sale(
        invoice_number=_generate_invoice_number(branch_id),
        branch_id=branch_id,
        created_by=user_id,
        prescription_id=data.get("prescription_id"),
        customer_name=data.get("customer_name"),
        customer_phone=data.get("customer_phone"),
        customer_age=data.get("customer_age"),
        subtotal=round(subtotal, 2),
        discount_amount=discount_amount,
        discount_percent=disc_pct,
        tax_amount=round(tax_total, 2),
        total_amount=total,
        amount_paid=amount_paid,
        change_given=max(change_given, 0),
        payment_method=data.get("payment_method", "cash"),
        payment_status="paid" if amount_paid >= total else "partial",
        notes=data.get("notes"),
    )

    for si in sale_items:
        sale.items.append(si)

    db.session.add(sale)
    db.session.commit()
    logger.info(f"Bill created: invoice={sale.invoice_number} total={sale.total_amount}")
    return sale


def get_sale(sale_id: int) -> Sale:
    return Sale.query.get_or_404(sale_id)


def get_sales(branch_id=None, from_date=None, to_date=None, page=1, per_page=20):
    query = Sale.query
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if from_date:
        query = query.filter(Sale.created_at >= from_date)
    if to_date:
        query = query.filter(Sale.created_at <= to_date)
    pagination = query.order_by(Sale.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return {
        "items": [s.to_dict(include_items=False) for s in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
        "per_page": per_page,
    }

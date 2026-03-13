from datetime import datetime, timezone
from database.db import db


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey("prescriptions.id"), nullable=True)

    # Customer
    customer_name = db.Column(db.String(120), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_age = db.Column(db.Integer, nullable=True)

    # Totals
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    discount_percent = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    amount_paid = db.Column(db.Float, default=0.0)
    change_given = db.Column(db.Float, default=0.0)

    payment_method = db.Column(db.String(30), default="cash")  # cash | card | upi | credit
    payment_status = db.Column(db.String(20), default="paid")  # paid | pending | partial
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    branch = db.relationship("Branch", back_populates="sales")
    created_by_user = db.relationship("User", back_populates="sales")
    prescription = db.relationship("Prescription", back_populates="sale")
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    def to_dict(self, include_items=True):
        data = {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "branch_id": self.branch_id,
            "branch_name": self.branch.name if self.branch else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_user.full_name if self.created_by_user else None,
            "prescription_id": self.prescription_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_age": self.customer_age,
            "subtotal": self.subtotal,
            "discount_amount": self.discount_amount,
            "discount_percent": self.discount_percent,
            "tax_amount": self.tax_amount,
            "total_amount": self.total_amount,
            "amount_paid": self.amount_paid,
            "change_given": self.change_given,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self):
        return f"<Sale {self.invoice_number} total={self.total_amount}>"


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=True)
    batch_number = db.Column(db.String(60), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    line_total = db.Column(db.Float, nullable=False)

    # Relationships
    sale = db.relationship("Sale", back_populates="items")
    medicine = db.relationship("Medicine", back_populates="sale_items")

    def to_dict(self):
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine.name if self.medicine else None,
            "generic_name": self.medicine.generic_name if self.medicine else None,
            "inventory_id": self.inventory_id,
            "batch_number": self.batch_number,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount_percent": self.discount_percent,
            "tax_percent": self.tax_percent,
            "line_total": self.line_total,
        }

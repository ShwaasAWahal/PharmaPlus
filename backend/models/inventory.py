from datetime import datetime, timezone, date
from database.db import db


class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=False, index=True)
    batch_number = db.Column(db.String(60), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, default=10)
    expiry_date = db.Column(db.Date, nullable=True, index=True)
    manufacture_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Float, nullable=True)
    selling_price = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(60), nullable=True)        # shelf/rack location
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    medicine = db.relationship("Medicine", back_populates="inventory_items")
    branch = db.relationship("Branch", back_populates="inventory_items")

    __table_args__ = (
        db.UniqueConstraint("medicine_id", "branch_id", "batch_number", name="uq_inventory_batch"),
    )

    @property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @property
    def days_to_expiry(self) -> int | None:
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.low_stock_threshold

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine.name if self.medicine else None,
            "generic_name": self.medicine.generic_name if self.medicine else None,
            "branch_id": self.branch_id,
            "branch_name": self.branch.name if self.branch else None,
            "batch_number": self.batch_number,
            "quantity": self.quantity,
            "low_stock_threshold": self.low_stock_threshold,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "manufacture_date": self.manufacture_date.isoformat() if self.manufacture_date else None,
            "purchase_price": self.purchase_price,
            "selling_price": self.selling_price,
            "location": self.location,
            "notes": self.notes,
            "is_expired": self.is_expired,
            "days_to_expiry": self.days_to_expiry,
            "is_low_stock": self.is_low_stock,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Inventory medicine={self.medicine_id} batch={self.batch_number} qty={self.quantity}>"

from datetime import datetime, timezone
from database.db import db


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    generic_name = db.Column(db.String(200), nullable=True, index=True)
    brand = db.Column(db.String(120), nullable=True)
    category = db.Column(db.String(80), nullable=True)        # e.g. Antibiotic, Analgesic
    form = db.Column(db.String(60), nullable=True)            # Tablet, Syrup, Injection
    strength = db.Column(db.String(60), nullable=True)        # e.g. 500mg, 250ml
    unit = db.Column(db.String(20), nullable=False, default="strip")
    barcode = db.Column(db.String(60), unique=True, nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)
    requires_prescription = db.Column(db.Boolean, default=False)
    hsn_code = db.Column(db.String(20), nullable=True)        # Harmonized System Nomenclature
    tax_percent = db.Column(db.Float, default=0.0)

    # Pricing
    purchase_price = db.Column(db.Float, nullable=False, default=0.0)
    selling_price = db.Column(db.Float, nullable=False, default=0.0)
    mrp = db.Column(db.Float, nullable=True)                  # Maximum Retail Price

    # Supplier
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    supplier = db.relationship("Supplier", back_populates="medicines")
    inventory_items = db.relationship("Inventory", back_populates="medicine", lazy="dynamic")
    sale_items = db.relationship("SaleItem", back_populates="medicine", lazy="dynamic")

    def to_dict(self, include_inventory=False):
        data = {
            "id": self.id,
            "name": self.name,
            "generic_name": self.generic_name,
            "brand": self.brand,
            "category": self.category,
            "form": self.form,
            "strength": self.strength,
            "unit": self.unit,
            "barcode": self.barcode,
            "description": self.description,
            "requires_prescription": self.requires_prescription,
            "hsn_code": self.hsn_code,
            "tax_percent": self.tax_percent,
            "purchase_price": self.purchase_price,
            "selling_price": self.selling_price,
            "mrp": self.mrp,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_inventory:
            data["inventory"] = [inv.to_dict() for inv in self.inventory_items]
        return data

    def __repr__(self):
        return f"<Medicine {self.name} ({self.strength})>"

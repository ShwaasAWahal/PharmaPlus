from datetime import datetime, timezone
from database.db import db


class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    license_number = db.Column(db.String(60), nullable=True)
    manager_name = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    users = db.relationship("User", back_populates="branch", lazy="dynamic")
    inventory_items = db.relationship("Inventory", back_populates="branch", lazy="dynamic")
    sales = db.relationship("Sale", back_populates="branch", lazy="dynamic")
    prescriptions = db.relationship("Prescription", back_populates="branch", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "license_number": self.license_number,
            "manager_name": self.manager_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Branch {self.name}>"

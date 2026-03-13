from datetime import datetime, timezone
from database.db import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    gstin = db.Column(db.String(20), nullable=True)          # GST / Tax ID
    license_number = db.Column(db.String(60), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)  # e.g. "Net 30"
    rating = db.Column(db.Float, default=0.0)                 # 0-5 performance rating
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    medicines = db.relationship("Medicine", back_populates="supplier", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "gstin": self.gstin,
            "license_number": self.license_number,
            "payment_terms": self.payment_terms,
            "rating": self.rating,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Supplier {self.name}>"

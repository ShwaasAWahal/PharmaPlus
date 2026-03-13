from datetime import datetime, timezone
from database.db import db


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Patient info
    patient_name = db.Column(db.String(120), nullable=True)
    patient_age = db.Column(db.Integer, nullable=True)
    patient_phone = db.Column(db.String(20), nullable=True)
    doctor_name = db.Column(db.String(120), nullable=True)
    doctor_registration = db.Column(db.String(60), nullable=True)

    # File
    file_path = db.Column(db.String(300), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(20), nullable=True)      # jpg | png | pdf

    # Processing status
    status = db.Column(db.String(30), default="pending")     # pending | processing | completed | failed
    ocr_result = db.Column(db.Text, nullable=True)           # JSON string from OCR service
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    branch = db.relationship("Branch", back_populates="prescriptions")
    uploaded_by_user = db.relationship("User", back_populates="prescriptions")
    sale = db.relationship("Sale", back_populates="prescription", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "branch_id": self.branch_id,
            "branch_name": self.branch.name if self.branch else None,
            "uploaded_by": self.uploaded_by,
            "uploaded_by_name": self.uploaded_by_user.full_name if self.uploaded_by_user else None,
            "patient_name": self.patient_name,
            "patient_age": self.patient_age,
            "patient_phone": self.patient_phone,
            "doctor_name": self.doctor_name,
            "doctor_registration": self.doctor_registration,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "status": self.status,
            "ocr_result": self.ocr_result,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Prescription id={self.id} status={self.status}>"

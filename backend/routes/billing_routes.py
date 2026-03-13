import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from services import billing_service
from utils.jwt_utils import get_current_user, role_required

logger = logging.getLogger(__name__)
billing_bp = Blueprint("billing", __name__, url_prefix="/api/billing")


@billing_bp.post("/bills")
@jwt_required()
def create_bill():
    """Create a new sale / bill."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    required = ["branch_id", "items"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        sale = billing_service.create_bill(data, user_id=user.id)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Bill creation error: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Could not create bill."}), 500

    return jsonify({
        "success": True,
        "message": "Bill created.",
        "invoice": sale.to_dict(include_items=True),
    }), 201


@billing_bp.get("/bills")
@jwt_required()
def list_bills():
    """List bills with optional filters."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    branch_id = request.args.get("branch_id", type=int)
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    result = billing_service.get_sales(
        branch_id=branch_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        per_page=per_page,
    )
    return jsonify({"success": True, **result}), 200


@billing_bp.get("/bills/<int:sale_id>")
@jwt_required()
def get_bill(sale_id):
    """Get a single bill / invoice."""
    sale = billing_service.get_sale(sale_id)
    return jsonify({"success": True, "invoice": sale.to_dict(include_items=True)}), 200


@billing_bp.get("/bills/<int:sale_id>/invoice")
@jwt_required()
def get_invoice_json(sale_id):
    """
    Generate a structured invoice JSON — ready for frontend rendering or PDF generation.
    """
    from models.branch import Branch
    sale = billing_service.get_sale(sale_id)
    branch = Branch.query.get(sale.branch_id)

    invoice = {
        "invoice_number": sale.invoice_number,
        "date": sale.created_at.strftime("%d %b %Y %H:%M") if sale.created_at else "",
        "pharmacy": {
            "name": branch.name if branch else "Pharmacy",
            "address": branch.address if branch else "",
            "phone": branch.phone if branch else "",
            "email": branch.email if branch else "",
            "license": branch.license_number if branch else "",
        },
        "customer": {
            "name": sale.customer_name or "Walk-in Customer",
            "phone": sale.customer_phone or "",
            "age": sale.customer_age,
        },
        "items": [
            {
                "sr": idx + 1,
                "medicine": item.medicine.name if item.medicine else "",
                "generic": item.medicine.generic_name if item.medicine else "",
                "batch": item.batch_number or "",
                "qty": item.quantity,
                "unit_price": item.unit_price,
                "discount_pct": item.discount_percent,
                "tax_pct": item.tax_percent,
                "line_total": item.line_total,
            }
            for idx, item in enumerate(sale.items)
        ],
        "subtotal": sale.subtotal,
        "discount_amount": sale.discount_amount,
        "discount_percent": sale.discount_percent,
        "tax_amount": sale.tax_amount,
        "total_amount": sale.total_amount,
        "amount_paid": sale.amount_paid,
        "change_given": sale.change_given,
        "payment_method": sale.payment_method,
        "payment_status": sale.payment_status,
        "served_by": sale.created_by_user.full_name if sale.created_by_user else "",
        "notes": sale.notes or "",
    }
    return jsonify({"success": True, "invoice": invoice}), 200


# ── Prescription upload ────────────────────────────────────────────────────────

@billing_bp.post("/prescription/upload")
@jwt_required()
def upload_prescription():
    """
    POST /api/billing/prescription/upload
    Upload a prescription image; actual OCR is handled externally.
    """
    import os
    from flask import current_app
    from werkzeug.utils import secure_filename
    from database.db import db
    from models.prescription import Prescription

    user = get_current_user()

    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "message": "Filename is empty."}), 400

    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "pdf"})
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        return jsonify({"success": False,
                        "message": f"File type .{ext} not allowed. Allowed: {allowed}"}), 400

    branch_id = request.form.get("branch_id", type=int) or user.branch_id
    if not branch_id:
        return jsonify({"success": False, "message": "branch_id is required."}), 400

    filename = secure_filename(file.filename)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    prescription = Prescription(
        branch_id=branch_id,
        uploaded_by=user.id,
        patient_name=request.form.get("patient_name"),
        patient_age=request.form.get("patient_age", type=int),
        patient_phone=request.form.get("patient_phone"),
        doctor_name=request.form.get("doctor_name"),
        file_path=file_path,
        file_name=filename,
        file_type=ext,
        status="pending",
        notes=request.form.get("notes"),
    )
    db.session.add(prescription)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Prescription uploaded. Pending OCR processing.",
        "prescription": prescription.to_dict(),
    }), 201


@billing_bp.get("/prescriptions")
@jwt_required()
def list_prescriptions():
    from models.prescription import Prescription
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    branch_id = request.args.get("branch_id", type=int)

    query = Prescription.query
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    pagination = query.order_by(Prescription.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "success": True,
        "prescriptions": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


@billing_bp.get("/prescriptions/<int:prescription_id>")
@jwt_required()
def get_prescription(prescription_id):
    from models.prescription import Prescription
    p = Prescription.query.get_or_404(prescription_id)
    return jsonify({"success": True, "prescription": p.to_dict()}), 200

"""
ML Integration Routes
─────────────────────
Placeholder endpoints that forward data to external ML services.
Currently return structured mock responses so the frontend and ML teams
can integrate independently.

Replace the mock logic in services/ml_proxy_service.py once the ML
service is deployed and ML_SERVICE_BASE_URL is configured.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from services import ml_proxy_service
from utils.jwt_utils import role_required

logger = logging.getLogger(__name__)
ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")


@ml_bp.post("/predict-demand")
@jwt_required()
def predict_demand():
    """
    POST /api/ml/predict-demand
    Predict future demand for a medicine at a branch.

    Body: { medicine_id, branch_id, horizon_days? }
    """
    data = request.get_json(silent=True) or {}
    medicine_id = data.get("medicine_id")
    branch_id = data.get("branch_id")

    if not medicine_id or not branch_id:
        return jsonify({
            "success": False,
            "message": "medicine_id and branch_id are required."
        }), 400

    result = ml_proxy_service.predict_demand(
        medicine_id=int(medicine_id),
        branch_id=int(branch_id),
        horizon_days=int(data.get("horizon_days", 30)),
    )
    return jsonify({"success": True, "prediction": result}), 200


@ml_bp.post("/recommend-generic")
@jwt_required()
def recommend_generic():
    """
    POST /api/ml/recommend-generic
    Suggest generic alternatives for a branded medicine.

    Body: { brand_medicine_name }
    """
    data = request.get_json(silent=True) or {}
    brand_name = (data.get("brand_medicine_name") or "").strip()

    if not brand_name:
        return jsonify({
            "success": False,
            "message": "brand_medicine_name is required."
        }), 400

    result = ml_proxy_service.recommend_generic(brand_name)
    return jsonify({"success": True, "recommendations": result}), 200


@ml_bp.post("/process-prescription")
@jwt_required()
def process_prescription():
    """
    POST /api/ml/process-prescription
    Submit a prescription (by ID) to the ML OCR/parsing service.

    Body: { prescription_id }
    """
    data = request.get_json(silent=True) or {}
    prescription_id = data.get("prescription_id")

    if not prescription_id:
        return jsonify({
            "success": False,
            "message": "prescription_id is required."
        }), 400

    from models.prescription import Prescription
    from database.db import db

    prescription = Prescription.query.get(int(prescription_id))
    if not prescription:
        return jsonify({"success": False, "message": "Prescription not found."}), 404

    # Mark as processing
    prescription.status = "processing"
    db.session.commit()

    result = ml_proxy_service.process_prescription(
        prescription_id=prescription.id,
        file_path=prescription.file_path,
    )

    # Store OCR result if available
    import json
    prescription.ocr_result = json.dumps(result)
    prescription.status = "completed" if result.get("extracted_medicines") else "failed"
    db.session.commit()

    return jsonify({"success": True, "result": result}), 200


@ml_bp.get("/status")
@jwt_required()
def ml_service_status():
    """Check if the ML service is reachable."""
    import requests
    from flask import current_app

    base_url = current_app.config.get("ML_SERVICE_BASE_URL", "")
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        return jsonify({
            "success": True,
            "ml_service": "reachable",
            "status_code": resp.status_code,
        }), 200
    except Exception as e:
        return jsonify({
            "success": True,
            "ml_service": "unreachable",
            "note": "Using mock responses.",
            "error": str(e),
        }), 200

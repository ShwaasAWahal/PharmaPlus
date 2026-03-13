import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)


def _ml_post(endpoint: str, payload: dict, timeout: int = None) -> dict:
    """Forward a request to the external ML service."""
    base_url = current_app.config.get("ML_SERVICE_BASE_URL", "")
    api_key = current_app.config.get("ML_SERVICE_API_KEY", "")
    timeout = timeout or current_app.config.get("ML_SERVICE_TIMEOUT", 30)

    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.exceptions.ConnectionError:
        logger.warning(f"ML service unreachable at {url} — returning mock response.")
        return {"success": False, "mock": True, "reason": "ML service not reachable"}
    except requests.exceptions.Timeout:
        logger.warning(f"ML service timeout at {url}")
        return {"success": False, "mock": True, "reason": "ML service timeout"}
    except requests.exceptions.HTTPError as e:
        logger.error(f"ML service HTTP error {e.response.status_code}: {e}")
        return {"success": False, "error": str(e)}


# ── Placeholder ML functions ───────────────────────────────────────────────────

def predict_demand(medicine_id: int, branch_id: int, horizon_days: int = 30) -> dict:
    """
    Predict future demand for a medicine in a branch.
    Forwards to ML service or returns a structured mock.
    """
    payload = {
        "medicine_id": medicine_id,
        "branch_id": branch_id,
        "horizon_days": horizon_days,
    }
    result = _ml_post("/predict-demand", payload)
    if result.get("mock"):
        return {
            "medicine_id": medicine_id,
            "branch_id": branch_id,
            "horizon_days": horizon_days,
            "predicted_units": 150,
            "confidence": 0.82,
            "model_version": "mock-v1",
            "note": "Mock response — ML service not connected.",
        }
    return result.get("data", {})


def recommend_generic(brand_medicine_name: str) -> dict:
    """
    Recommend generic alternatives for a branded medicine.
    Forwards to ML service or returns a structured mock.
    """
    payload = {"brand_medicine_name": brand_medicine_name}
    result = _ml_post("/recommend-generic", payload)
    if result.get("mock"):
        return {
            "brand_medicine": brand_medicine_name,
            "generics": [
                {"name": "Generic Alternative A", "price_saving_pct": 45, "available": True},
                {"name": "Generic Alternative B", "price_saving_pct": 38, "available": True},
            ],
            "note": "Mock response — ML service not connected.",
        }
    return result.get("data", {})


def process_prescription(prescription_id: int, file_path: str) -> dict:
    """
    Submit a prescription image to the ML service for OCR/parsing.
    Forwards to ML service or returns a structured mock.
    """
    payload = {
        "prescription_id": prescription_id,
        "file_path": file_path,
    }
    result = _ml_post("/process-prescription", payload)
    if result.get("mock"):
        return {
            "prescription_id": prescription_id,
            "status": "mock_processed",
            "extracted_medicines": [
                {"name": "Mock Medicine A", "dosage": "500mg", "frequency": "twice daily"},
                {"name": "Mock Medicine B", "dosage": "250mg", "frequency": "once daily"},
            ],
            "doctor_name": "Dr. Mock",
            "patient_name": "Mock Patient",
            "note": "Mock response — ML service not connected.",
        }
    return result.get("data", {})

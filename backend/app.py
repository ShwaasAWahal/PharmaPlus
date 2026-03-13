import logging
import os
from flask import Flask, jsonify

from config import get_config
from extensions import jwt, mail
from database.db import init_db
from utils.scheduler import init_scheduler

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    app = Flask(__name__)

    # ── Config ─────────────────────────────────────────────────────────────────
    app.config.from_object(config or get_config())

    # ── Extensions ─────────────────────────────────────────────────────────────
    jwt.init_app(app)
    mail.init_app(app)

    # ── Database ───────────────────────────────────────────────────────────────
    init_db(app)

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from routes.auth_routes import auth_bp
    from routes.medicine_routes import medicine_bp
    from routes.inventory_routes import inventory_bp
    from routes.billing_routes import billing_bp
    from routes.analytics_routes import analytics_bp
    from routes.ml_routes import ml_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(medicine_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ml_bp)

    # ── Scheduler ──────────────────────────────────────────────────────────────
    if not app.config.get("TESTING"):
        try:
            init_scheduler(app)
        except Exception as e:
            logger.warning(f"Scheduler init failed (non-fatal): {e}")

    # ── JWT callbacks ──────────────────────────────────────────────────────────
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "message": "Invalid token."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "message": "Authorization token required."}), 401

    # ── Error handlers ─────────────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "message": "Bad request.", "detail": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"success": False, "message": "Unauthorized."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"success": False, "message": "Forbidden."}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Internal server error."}), 500

    # ── Health check ───────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return jsonify({
            "success": True,
            "status": "healthy",
            "service": "AI Pharmacy Management API",
            "version": "1.0.0",
        }), 200

    @app.get("/")
    def root():
        return jsonify({
            "message": "AI-Powered Pharmacy Management API",
            "docs": "/api/health",
            "version": "1.0.0",
        }), 200

    logger.info("Flask app created successfully.")
    return app


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)

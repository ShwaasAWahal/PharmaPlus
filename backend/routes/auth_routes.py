import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt, create_access_token
)

from database.db import db
from models.user import User
from models.branch import Branch
from utils.jwt_utils import generate_tokens, role_required, get_current_user

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _validate_password(password: str) -> str | None:
    """Return error message or None if valid."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


@auth_bp.post("/register")
@jwt_required()
@role_required("admin")
def register():
    """Admin-only: register a new user."""
    data = request.get_json(silent=True) or {}
    required = ["full_name", "email", "password", "role"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing)}"}), 400

    if data["role"] not in ("admin", "pharmacist"):
        return jsonify({"success": False, "message": "role must be 'admin' or 'pharmacist'"}), 400

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"success": False, "message": "Email already registered."}), 409

    err = _validate_password(data["password"])
    if err:
        return jsonify({"success": False, "message": err}), 400

    branch_id = data.get("branch_id")
    if branch_id and not Branch.query.get(branch_id):
        return jsonify({"success": False, "message": "Branch not found."}), 404

    user = User(
        full_name=data["full_name"].strip(),
        email=data["email"].lower().strip(),
        role=data["role"],
        branch_id=branch_id,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    logger.info(f"New user registered: {user.email} role={user.role}")
    return jsonify({"success": True, "message": "User registered.", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    """Authenticate and receive JWT tokens."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    tokens = generate_tokens(user)
    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": user.to_dict(),
        **tokens,
    }), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using a refresh token."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    if not user or not user.is_active:
        return jsonify({"success": False, "message": "User not found or inactive."}), 401

    from utils.jwt_utils import generate_tokens
    tokens = generate_tokens(user)
    return jsonify({"success": True, **tokens}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    """Return the current user's profile."""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
    return jsonify({"success": True, "user": user.to_dict()}), 200


@auth_bp.put("/me/password")
@jwt_required()
def change_password():
    """Change the current user's password."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")

    if not user.check_password(old_pw):
        return jsonify({"success": False, "message": "Old password is incorrect."}), 400

    err = _validate_password(new_pw)
    if err:
        return jsonify({"success": False, "message": err}), 400

    user.set_password(new_pw)
    db.session.commit()
    return jsonify({"success": True, "message": "Password changed successfully."}), 200


# ── User management (admin) ────────────────────────────────────────────────────

@auth_bp.get("/users")
@jwt_required()
@role_required("admin")
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    branch_id = request.args.get("branch_id", type=int)

    query = User.query
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "success": True,
        "users": [u.to_dict() for u in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
    }), 200


@auth_bp.put("/users/<int:user_id>")
@jwt_required()
@role_required("admin")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        user.full_name = data["full_name"].strip()
    if "role" in data and data["role"] in ("admin", "pharmacist"):
        user.role = data["role"]
    if "branch_id" in data:
        user.branch_id = data["branch_id"]
    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()}), 200


@auth_bp.delete("/users/<int:user_id>")
@jwt_required()
@role_required("admin")
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return jsonify({"success": True, "message": "User deactivated."}), 200

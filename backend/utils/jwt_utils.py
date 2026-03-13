import logging
from functools import wraps
from datetime import datetime, timezone

import jwt
from flask import current_app, request, jsonify

logger = logging.getLogger(__name__)


def generate_tokens(user) -> dict:
    """Generate access and refresh JWT tokens for a user."""
    from flask_jwt_extended import create_access_token, create_refresh_token

    identity = str(user.id)
    additional_claims = {
        "role": user.role,
        "branch_id": user.branch_id,
        "email": user.email,
        "full_name": user.full_name,
    }

    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=identity)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


def role_required(*roles):
    """Decorator that restricts access to users with certain roles."""
    from flask_jwt_extended import get_jwt, verify_jwt_in_request

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({
                    "success": False,
                    "message": f"Access denied. Required roles: {', '.join(roles)}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """Return the User object for the current JWT identity."""
    from flask_jwt_extended import get_jwt_identity
    from models.user import User

    user_id = get_jwt_identity()
    if not user_id:
        return None
    return User.query.get(int(user_id))


def get_current_claims():
    """Return all JWT claims for the current request."""
    from flask_jwt_extended import get_jwt
    return get_jwt()

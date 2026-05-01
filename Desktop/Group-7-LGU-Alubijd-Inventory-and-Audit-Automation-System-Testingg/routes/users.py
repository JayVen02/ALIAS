from flask import Blueprint, session, request
from extensions import mysql
from routes.auth import login_required, admin_required
from services.user_service import (
    get_all_users,
    create_user,
    update_user,
    delete_user,
    validate_user_payload,
    VALID_ROLES,
)

users_bp = Blueprint("users", __name__, url_prefix="/api")


@users_bp.route("/users", methods=["GET"])
@login_required
def api_get_users():
    return {"users": get_all_users(mysql)}


@users_bp.route("/users", methods=["POST"])
@admin_required
def api_add_user():
    data     = request.json or {}
    email    = data.get("email", "").strip()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    role     = data.get("role", "staff")

    if role not in VALID_ROLES:
        return {"error": "Invalid role. Must be 'admin' or 'staff'."}, 400

    error = validate_user_payload(email, password, require_password=True)
    if error:
        return {"error": error}, 400

    try:
        new_id = create_user(mysql, email, password, full_name, role)
        mysql.connection.commit()
        return {"message": "Account created successfully", "id": new_id}, 201
    except Exception as exc:
        return {"error": str(exc)}, 500


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def api_update_user(user_id):
    data     = request.json or {}
    email    = data.get("email", "").strip()
    full_name = data.get("full_name", "").strip()
    role     = data.get("role", "staff")
    password = data.get("password", "")

    error = validate_user_payload(email, password, require_password=False)
    if error:
        return {"error": error}, 400

    try:
        update_user(mysql, user_id, email, full_name, role, password or None)
        mysql.connection.commit()
        return {"message": "User updated successfully"}
    except Exception as exc:
        return {"error": str(exc)}, 500


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def api_delete_user(user_id):
    try:
        delete_user(mysql, user_id)
        mysql.connection.commit()
        return {"message": "User deleted successfully"}
    except Exception as exc:
        mysql.connection.rollback()
        return {"error": f"Cannot delete user: {str(exc)}"}, 500

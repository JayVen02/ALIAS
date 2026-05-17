from flask import Blueprint, session, request
from extensions import mysql
from routes.auth import login_required, admin_required
from services.audit_service import log_action
from services.inventory_service import (
    get_all_categories,
    get_all_subcategories,
    get_items,
    create_item,
    update_item,
    delete_item,
    serialize_item,
    find_item_by_name,
    add_quantity_to_item,
)
from services.approval_service import ensure_requests_table, submit_request
import json

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api")


def _is_admin():
    return session.get("role") == "admin"


@inventory_bp.route("/categories", methods=["GET"])
@login_required
def api_categories():
    try:
        return {"categories": get_all_categories(mysql)}
    except Exception as exc:
        return {"error": str(exc)}, 500


@inventory_bp.route("/subcategories", methods=["GET"])
@login_required
def api_subcategories():
    try:
        return {"subcategories": get_all_subcategories(mysql)}
    except Exception as exc:
        return {"error": str(exc)}, 500


@inventory_bp.route("/inventory", methods=["GET"])
@login_required
def api_get_inventory():
    try:
        items = get_items(
            mysql,
            category_id    = request.args.get("category_id"),
            subcategory_id = request.args.get("subcategory_id"),
            search         = request.args.get("search"),
            sort           = request.args.get("sort", "latest"),
        )
        return {"items": [serialize_item(i) for i in items]}
    except Exception as exc:
        return {"error": str(exc)}, 500


@inventory_bp.route("/inventory", methods=["POST"])
@login_required
def api_create_item():
    data = request.json or {}

    name = (data.get("name") or "").strip()
    category_id    = data.get("category_id")
    subcategory_id = data.get("subcategory_id")

    if not name or not category_id or not subcategory_id:
        return {"error": "Missing required fields."}, 400

    quantity     = data.get("quantity", 0)
    stock_number = data.get("stock_number")

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        try:
            quantity = int(stock_number)
        except (TypeError, ValueError):
            quantity = 0

    # ── Non-admin: submit for approval ──
    if not _is_admin():
        ensure_requests_table(mysql)
        reason = (data.get("reason") or "").strip() or None
        payload = {
            "name": name,
            "category_id": category_id,
            "subcategory_id": subcategory_id,
            "quantity": quantity,
            "stock_number": stock_number,
        }
        req_id = submit_request(
            mysql,
            item_id=None,
            requested_by=session["user_id"],
            action_type="CREATE",
            payload=payload,
            reason=reason,
        )
        return {
            "pending": True,
            "request_id": req_id,
            "message": "Your request to add this item has been submitted and is pending admin approval.",
        }, 202

    # ── Admin: apply immediately ──
    existing = find_item_by_name(mysql, name, category_id, subcategory_id)

    if existing:
        item_id = existing["id"]

        # Add quantity to existing item
        add_quantity_to_item(mysql, item_id, quantity)

        log_action(
            mysql,
            item_id,
            session.get("user_id"),
            "QUANTITY_ADJUST",
            new_value=str(data),
        )

        mysql.connection.commit()

        return {
            "id": item_id,
            "updated": True,
            "message": "Existing item quantity updated.",
        }, 200

    # Create new item
    new_id = create_item(
        mysql,
        category_id,
        subcategory_id,
        name,
        quantity,
        stock_number,
    )

    log_action(
        mysql,
        new_id,
        session.get("user_id"),
        "CREATE",
        new_value=str(data),
    )

    mysql.connection.commit()

    return {
        "id": new_id,
        "updated": False,
        "message": "New item created.",
    }, 201


@inventory_bp.route("/inventory/<int:item_id>", methods=["PUT"])
@login_required
def api_update_item(item_id):
    data = request.json or {}

    # Sync quantity from stock_number
    if "stock_number" in data:
        try:
            data["quantity"] = int(data["stock_number"])
        except (TypeError, ValueError):
            pass

    # ── Non-admin: submit for approval ──
    if not _is_admin():
        ensure_requests_table(mysql)
        reason = (data.pop("reason", None) or "").strip() or None
        req_id = submit_request(
            mysql,
            item_id=item_id,
            requested_by=session["user_id"],
            action_type="UPDATE",
            payload=data,
            reason=reason,
        )
        return {
            "pending": True,
            "request_id": req_id,
            "message": "Your edit request has been submitted and is pending admin approval.",
        }, 202

    # ── Admin: apply immediately ──
    updated = update_item(mysql, item_id, data)
    if not updated:
        return {"error": "No valid fields to update."}, 400
    log_action(mysql, item_id, session.get("user_id"), "UPDATE", new_value=str(data))
    mysql.connection.commit()
    return {"message": "Updated"}


@inventory_bp.route("/inventory/<int:item_id>", methods=["DELETE"])
@login_required
def api_delete_item(item_id):
    data = request.json or {}

    # ── Non-admin: submit for approval ──
    if not _is_admin():
        ensure_requests_table(mysql)
        reason = (data.get("reason") or "").strip() or None
        req_id = submit_request(
            mysql,
            item_id=item_id,
            requested_by=session["user_id"],
            action_type="DELETE",
            payload={"item_id": item_id},
            reason=reason,
        )
        return {
            "pending": True,
            "request_id": req_id,
            "message": "Your delete request has been submitted and is pending admin approval.",
        }, 202

    # ── Admin: apply immediately ──
    log_action(mysql, item_id, session.get("user_id"), "DELETE")
    delete_item(mysql, item_id)
    mysql.connection.commit()
    return {"message": "Deleted"}

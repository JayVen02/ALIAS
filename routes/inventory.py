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
)

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api")


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
<<<<<<< HEAD
    new_id = create_item(
        mysql,
        data.get("category_id"),
        data.get("subcategory_id"),
        data.get("name"),
        data.get("quantity", 0),
    )
    log_action(mysql, new_id, session.get("user_id"), "CREATE", new_value=str(data))
    mysql.connection.commit()
    return {"id": new_id}, 201

=======

    name = (data.get("name") or "").strip()
    category_id = data.get("category_id")
    subcategory_id = data.get("subcategory_id")


    if not name or not category_id or not subcategory_id:
        return {"error": "Missing required fields."}, 400

    quantity = data.get("quantity", 0)
    stock_number = data.get("stock_number")

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        # If quantity is not a valid int, try to parse from stock_number
        try:
            quantity = int(stock_number)
        except (TypeError, ValueError):
            quantity = 0

    new_id = create_item(
        mysql,
        category_id,
        subcategory_id,
        name,
        quantity,
        stock_number
    )

    log_action(mysql, new_id, session.get("user_id"), "CREATE", new_value=str(data))
    mysql.connection.commit()

    return {"id": new_id}, 201
>>>>>>> 9fa0d723e2752acd617c4a3b19e0d774d0108fe0

@inventory_bp.route("/inventory/<int:item_id>", methods=["PUT"])
@login_required
def api_update_item(item_id):
    data = request.json or {}
<<<<<<< HEAD
=======
    
    # If stock_number is being updated, sync quantity
    if "stock_number" in data:
        try:
            data["quantity"] = int(data["stock_number"])
        except (TypeError, ValueError):
            pass

>>>>>>> 9fa0d723e2752acd617c4a3b19e0d774d0108fe0
    updated = update_item(mysql, item_id, data)
    if not updated:
        return {"error": "No valid fields to update."}, 400
    log_action(mysql, item_id, session.get("user_id"), "UPDATE", new_value=str(data))
    mysql.connection.commit()
    return {"message": "Updated"}


@inventory_bp.route("/inventory/<int:item_id>", methods=["DELETE"])
@login_required
def api_delete_item(item_id):
    log_action(mysql, item_id, session.get("user_id"), "DELETE")
    delete_item(mysql, item_id)
    mysql.connection.commit()
    return {"message": "Deleted"}

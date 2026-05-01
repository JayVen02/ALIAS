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
    get_item_by_details,
    add_quantity_to_item,
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
    category_id = data.get("category_id")
    subcategory_id = data.get("subcategory_id")
    name = data.get("name")
    quantity = data.get("quantity", 0)
    
    # Check if item with same name, category, and subcategory already exists
    existing_item = get_item_by_details(mysql, category_id, subcategory_id, name)
    
    if existing_item:
        # Item exists - add quantity to existing item
        item_id = existing_item["id"]
        new_quantity = add_quantity_to_item(mysql, item_id, quantity)
        log_action(
            mysql, 
            item_id, 
            session.get("user_id"), 
            "QUANTITY_ADJUST", 
            new_value=f"Added {quantity} units. New total: {new_quantity}"
        )
        mysql.connection.commit()
        return {
            "id": item_id, 
            "action": "updated",
            "message": f"Item quantity successfully added! New total: {new_quantity} units"
        }, 200
    else:
        # Item doesn't exist - create new item
        new_id = create_item(mysql, category_id, subcategory_id, name, quantity)
        log_action(mysql, new_id, session.get("user_id"), "CREATE", new_value=str(data))
        mysql.connection.commit()
        return {
            "id": new_id, 
            "action": "created",
            "message": f"New item '{name}' created successfully!"
        }, 201


@inventory_bp.route("/inventory/<int:item_id>", methods=["PUT"])
@login_required
def api_update_item(item_id):
    data = request.json or {}
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

"""
routes/approvals.py
API endpoints for the inventory-change-request approval workflow.

Staff roles  → POST  /api/requests               (submit a change request)
Admin only   → GET   /api/requests               (list pending / all)
             → POST  /api/requests/<id>/approve  (approve)
             → POST  /api/requests/<id>/reject   (reject)
             → GET   /api/requests/count         (badge count)
"""

import json
from flask import Blueprint, session, request

from extensions import mysql
from routes.auth import login_required, admin_required
from services.approval_service import (
    ensure_requests_table,
    submit_request,
    get_pending_requests,
    get_all_requests,
    get_request_by_id,
    count_pending,
    approve_request,
    reject_request,
)
from services.inventory_service import (
    create_item,
    update_item,
    delete_item,
    serialize_item,
    get_items,
)
from services.audit_service import log_action

approvals_bp = Blueprint("approvals", __name__, url_prefix="/api")


def _ensure_table():
    ensure_requests_table(mysql)


# ── Staff: submit a change request ───────────────────────────────────────────

@approvals_bp.route("/requests", methods=["POST"])
@login_required
def api_submit_request():
    _ensure_table()
    data = request.json or {}

    action_type = (data.get("action_type") or "").upper()
    if action_type not in ("CREATE", "UPDATE", "DELETE"):
        return {"error": "Invalid action_type. Must be CREATE, UPDATE, or DELETE."}, 400

    item_id = data.get("item_id")
    payload = data.get("payload") or {}
    reason  = (data.get("reason") or "").strip() or None

    # Basic validation
    if action_type in ("UPDATE", "DELETE") and not item_id:
        return {"error": "item_id is required for UPDATE/DELETE requests."}, 400
    if action_type == "CREATE":
        p = payload if isinstance(payload, dict) else json.loads(payload)
        if not p.get("name") or not p.get("category_id") or not p.get("subcategory_id"):
            return {"error": "CREATE payload must include name, category_id, subcategory_id."}, 400

    req_id = submit_request(
        mysql,
        item_id=item_id,
        requested_by=session["user_id"],
        action_type=action_type,
        payload=payload,
        reason=reason,
    )
    return {"id": req_id, "message": "Change request submitted. Awaiting admin approval."}, 201


# ── Admin: list requests ──────────────────────────────────────────────────────

@approvals_bp.route("/requests", methods=["GET"])
@admin_required
def api_list_requests():
    _ensure_table()
    status_filter = request.args.get("status", "pending")
    if status_filter == "pending":
        rows = get_pending_requests(mysql)
    else:
        rows = get_all_requests(mysql)

    def _ser(r):
        d = dict(r)
        for k in ("created_at", "reviewed_at"):
            if d.get(k):
                d[k] = d[k].strftime("%Y-%m-%d %H:%M")
        # Safely parse payload for display
        try:
            if isinstance(d.get("payload"), str):
                d["payload_parsed"] = json.loads(d["payload"])
            else:
                d["payload_parsed"] = d.get("payload") or {}
        except Exception:
            d["payload_parsed"] = {}
        return d

    return {"requests": [_ser(r) for r in rows]}


# ── Admin: pending count (badge) ─────────────────────────────────────────────

@approvals_bp.route("/requests/count", methods=["GET"])
@login_required
def api_pending_count():
    _ensure_table()
    if session.get("role") != "admin":
        return {"count": 0}
    return {"count": count_pending(mysql)}


# ── Admin: approve a request ──────────────────────────────────────────────────

@approvals_bp.route("/requests/<int:req_id>/approve", methods=["POST"])
@admin_required
def api_approve_request(req_id):
    _ensure_table()
    data = request.json or {}
    review_note = (data.get("review_note") or "").strip() or None

    req = get_request_by_id(mysql, req_id)
    if not req:
        return {"error": "Request not found."}, 404
    if req["status"] != "pending":
        return {"error": f"Request is already {req['status']}."}, 409

    # Apply the change
    payload = req["payload"]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}

    action = req["action_type"]
    admin_id = session["user_id"]

    try:
        if action == "CREATE":
            p = payload
            # Sync quantity from stock_number if needed
            qty = p.get("quantity", 0)
            if not qty and p.get("stock_number"):
                try:
                    qty = int(p["stock_number"])
                except (TypeError, ValueError):
                    qty = 0
            new_id = create_item(
                mysql,
                p["category_id"],
                p["subcategory_id"],
                p["name"],
                qty,
                p.get("stock_number"),
            )
            log_action(mysql, new_id, admin_id, "CREATE",
                       new_value=f"[Approved request #{req_id}] {json.dumps(p)}")
            mysql.connection.commit()

        elif action == "UPDATE":
            # If stock_number in payload, sync quantity
            if "stock_number" in payload:
                try:
                    payload["quantity"] = int(payload["stock_number"])
                except (TypeError, ValueError):
                    pass
            update_item(mysql, req["item_id"], payload)
            log_action(mysql, req["item_id"], admin_id, "UPDATE",
                       new_value=f"[Approved request #{req_id}] {json.dumps(payload)}")
            mysql.connection.commit()

        elif action == "DELETE":
            log_action(mysql, req["item_id"], admin_id, "DELETE",
                       new_value=f"[Approved request #{req_id}]")
            delete_item(mysql, req["item_id"])
            mysql.connection.commit()

    except Exception as exc:
        return {"error": f"Failed to apply change: {str(exc)}"}, 500

    # Mark the request as approved
    approve_request(mysql, req_id, admin_id, review_note)
    return {"message": "Request approved and changes applied."}


# ── Admin: reject a request ───────────────────────────────────────────────────

@approvals_bp.route("/requests/<int:req_id>/reject", methods=["POST"])
@admin_required
def api_reject_request(req_id):
    _ensure_table()
    data = request.json or {}
    review_note = (data.get("review_note") or "").strip() or None

    req = get_request_by_id(mysql, req_id)
    if not req:
        return {"error": "Request not found."}, 404
    if req["status"] != "pending":
        return {"error": f"Request is already {req['status']}."}, 409

    reject_request(mysql, req_id, session["user_id"], review_note)
    return {"message": "Request rejected."}

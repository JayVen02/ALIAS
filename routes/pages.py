import datetime
import os
from flask import Blueprint, session, request, redirect, url_for, render_template, flash, jsonify

from extensions import mysql
from routes.auth import login_required, admin_required
from services.audit_service import ensure_audit_log_table
from services.inventory_service import get_recent_items
from services.approval_service import ensure_requests_table, get_all_requests, count_pending
from services.user_service import (
    get_user_by_email,
    get_all_users,
    update_profile,
    update_profile_picture,
)

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
@login_required
def dashboard():
    recent_items = get_recent_items(mysql, limit=5)
    return render_template("index.html", recent_items=recent_items)


@pages_bp.route("/inventory")
@login_required
def inventory():
    return render_template("inventory.html")


@pages_bp.route("/audit")
@login_required
def audit():
    ensure_audit_log_table(mysql, session.get("user_id"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    return render_template("audit.html", categories=categories)


@pages_bp.route("/api/dashboard-chart-data")
@login_required
def dashboard_chart_data():
    """Return monthly inventory quantity totals for ALL categories."""
    current_year = datetime.datetime.now().year
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name ASC")
    categories = cur.fetchall()

    result = {}
    current_month = datetime.datetime.now().month

    for cat in categories:
        cat_id = cat["id"]
        cat_name = cat["name"]
        safe_key = cat_name.lower().replace(" ", "_").replace("&", "and")

        cur.execute(
            """
            SELECT MONTH(i.date_created) AS month,
                   COALESCE(SUM(i.quantity), 0) AS total_qty
            FROM inventory_items i
            WHERE i.category_id = %s
              AND YEAR(i.date_created) = %s
            GROUP BY MONTH(i.date_created)
            ORDER BY month
            """,
            (cat_id, current_year),
        )
        rows = cur.fetchall()
        monthly = {int(row["month"]): int(row["total_qty"]) for row in rows}

        full_year_data = [monthly.get(m, 0) for m in range(1, 13)]
        result[safe_key] = {
            "name": cat_name.title(),
            "data": full_year_data[:current_month]
        }

    return jsonify({
        "labels": month_labels[:current_month],
        "datasets": result,
        "year": current_year,
    })

@pages_bp.route("/audit/<category_name>")
@login_required
def audit_form(category_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    cat = cur.fetchone()

    filtered_items = []
    if cat:
        cur.execute(
            """SELECT i.*, c.name AS category_name, s.name AS subcategory_name
               FROM inventory_items i
               JOIN categories c ON i.category_id = c.id
               JOIN subcategories s ON i.subcategory_id = s.id
               WHERE i.category_id = %s""",
            (cat["id"],),
        )
        filtered_items = cur.fetchall()

    return render_template("audit_form.html", category_name=category_name, items=filtered_items)


@pages_bp.route("/audit/history/<category_name>")
@login_required
def audit_category_history(category_name):
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT
               DATE(l.created_at) AS audit_date,
               c.name AS category_name,
               s.name AS subcategory_name,
               COUNT(*) AS activity_count
           FROM audit_logs l
           JOIN inventory_items i ON l.item_id = i.id
           JOIN categories c ON i.category_id = c.id
           JOIN subcategories s ON i.subcategory_id = s.id
           WHERE c.name = %s
           GROUP BY audit_date, category_name, subcategory_name
           ORDER BY audit_date DESC
           LIMIT 50""",
        (category_name,),
    )
    history = cur.fetchall()
    return render_template("audit_history.html", category_name=category_name, audit_history=history)


@pages_bp.route("/history")
@login_required
def history():
    ensure_audit_log_table(mysql, session.get("user_id"))

    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT l.*, COALESCE(u.full_name, u.email) AS officer_name, 
                  c.name AS category_name, i.name AS item_name, s.name AS subcategory_name
           FROM audit_logs l
           JOIN users u ON l.user_id = u.id
           LEFT JOIN inventory_items i ON l.item_id = i.id
           LEFT JOIN categories c ON i.category_id = c.id
           LEFT JOIN subcategories s ON i.subcategory_id = s.id
           ORDER BY l.created_at DESC
           LIMIT 50""",
    )
    logs = cur.fetchall()
    return render_template("history.html", logs=logs)


@pages_bp.route("/manage-accounts")
@admin_required
def manage_accounts():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, email, full_name, role, created_at FROM users ORDER BY created_at DESC"
    )
    staff_users = cur.fetchall()
    return render_template("manage_accounts.html", staff_users=staff_users)


@pages_bp.route("/approvals")
@admin_required
def approvals():
    ensure_requests_table(mysql)
    requests_list = get_all_requests(mysql)
    pending_count = count_pending(mysql)
    return render_template(
        "pending_requests.html",
        requests_list=requests_list,
        pending_count=pending_count,
    )


@pages_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    email = session["email"]

    if request.method == "POST":
        try:
            update_profile(
                mysql,
                email,
                full_name = request.form.get("full_name"),
                email     = request.form.get("email"),
                age       = request.form.get("age"),
                birthdate = request.form.get("birthdate"),
                address   = request.form.get("address"),
                contact   = request.form.get("contact"),
                skills    = request.form.get("skills"),
                work      = request.form.get("work"),
            )
            mysql.connection.commit()
            flash("Profile updated successfully!")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating profile: {str(e)}")
        
        return redirect(url_for("pages.profile"))

    user = get_user_by_email(mysql, email)
    return render_template("profile.html", user=user)


@pages_bp.route("/profile/upload", methods=["POST"])
@login_required
def upload_profile_pic():
    file = request.files.get("profile_pic")
    if not file or file.filename == "":
        return redirect(url_for("pages.profile"))

    # ── Validate extension ────────────────────────────────────────────────────
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        flash("Invalid file type. Only PNG, JPG, GIF, WEBP images are allowed.")
        return redirect(url_for("pages.profile"))

    # ── Validate MIME type by reading the magic bytes (first 12 bytes) ────────
    ALLOWED_MIME_SIGNATURES = {
        b"\x89PNG",                           # PNG
        b"\xff\xd8\xff",                      # JPEG/JPG
        b"GIF87a", b"GIF89a",                 # GIF
        b"RIFF",                              # WEBP (starts RIFF....WEBP)
    }
    header = file.read(12)
    file.seek(0)  # reset stream after reading
    mime_ok = any(header.startswith(sig) for sig in ALLOWED_MIME_SIGNATURES)
    # Special WEBP check: RIFF????WEBP
    if header.startswith(b"RIFF") and b"WEBP" not in header:
        mime_ok = False
    if not mime_ok:
        flash("File content does not match a supported image type.")
        return redirect(url_for("pages.profile"))

    email = session["email"]
    upload_dir = os.path.join("static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # Sanitize filename — derive from session email (no user-controlled path)
    safe_email = email.replace("@", "_").replace(".", "_")
    filename = f"profile_{safe_email}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    update_profile_picture(mysql, email, filepath)
    mysql.connection.commit()
    return redirect(url_for("pages.profile"))
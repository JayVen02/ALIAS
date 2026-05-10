from functools import wraps
from flask import Blueprint, session, request, redirect, url_for, flash, render_template
from extensions import mysql
from services.user_service import get_user_by_login, hash_password, verify_password

auth_bp = Blueprint("auth", __name__)


# ── Decorators ────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "logged_in" not in session:
            if request.path.startswith("/api/"):
                return {"error": "Authentication required"}, 401
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "logged_in" not in session:
            if request.path.startswith("/api/"):
                return {"error": "Authentication required"}, 401
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            if request.path.startswith("/api/"):
                return {"error": "Admin privileges required"}, 403
            flash("Access denied. Admin privileges required.")
            return redirect(url_for("pages.dashboard"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("email", "").strip()
        password   = request.form.get("password", "")

        # Basic server-side input validation
        if not identifier or not password:
            flash("Email and password are required.")
            return redirect(url_for("auth.login"))

        if len(identifier) > 254 or len(password) > 256:
            flash("Invalid credentials.")
            return redirect(url_for("auth.login"))

        user = get_user_by_login(mysql, identifier)

        if user and verify_password(user["password"], password):
            # ── Opportunistic re-hash of legacy plaintext passwords ──────────
            stored = user["password"]
            if not (stored.startswith("pbkdf2:") or stored.startswith("scrypt:")):
                cur = mysql.connection.cursor()
                cur.execute(
                    "UPDATE users SET password=%s WHERE id=%s",
                    (hash_password(password), user["id"]),
                )
                mysql.connection.commit()

            session.clear()
            session.permanent = True          # honour PERMANENT_SESSION_LIFETIME
            session["logged_in"] = True
            session["email"]     = user.get("email", "")
            session["full_name"] = user.get("full_name") or user.get("email")
            session["user_id"]   = user["id"]
            session["role"]      = user.get("role", "staff")
            return redirect(url_for("pages.dashboard"))

        # Generic error — don't reveal whether email exists
        flash("Invalid email or password.")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

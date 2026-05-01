from functools import wraps
from flask import Blueprint, session, request, redirect, url_for, flash, render_template
from extensions import mysql
from services.user_service import get_user_by_login

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

        user = get_user_by_login(mysql, identifier)

        if user and user["password"] == password:
            session.clear()
            session["logged_in"] = True
            session["email"]     = user.get("email", "")
            session["full_name"] = user.get("full_name") or user.get("email")
            session["user_id"]   = user["id"]
            session["role"]      = user.get("role", "staff")
            return redirect(url_for("pages.dashboard"))

        if user:
            flash("Incorrect password. Please try again.")
        else:
            flash("No account found with that email address.")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

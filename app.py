import os
import time
import threading
from collections import defaultdict

from flask import Flask, request, jsonify, g
from config import Config
from extensions import mysql
from routes.auth import auth_bp
from routes.pages import pages_bp
from routes.inventory import inventory_bp
from routes.users import users_bp
from routes.pdf import pdf_bp
from routes.approvals import approvals_bp


# ── Simple in-memory brute-force tracker ─────────────────────────────────────
# { ip: [timestamp, ...] }
_login_attempts: dict = defaultdict(list)
_lock = threading.Lock()


def _is_rate_limited(ip: str, max_attempts: int, window_secs: int) -> bool:
    """Return True if `ip` has exceeded `max_attempts` within `window_secs`."""
    now = time.time()
    with _lock:
        # Prune old entries
        _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < window_secs]
        if len(_login_attempts[ip]) >= max_attempts:
            return True
        _login_attempts[ip].append(now)
        return False


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    mysql.init_app(app)

    # ── Secure HTTP headers on every response ─────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Stop MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Enable browser XSS filter (legacy)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Content-Security-Policy — tightened for this app's known CDNs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; "
            "img-src 'self' data: https://res.cloudinary.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Permissions Policy — disable unused browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        # Remove server fingerprint
        response.headers.pop("Server", None)
        return response

    # ── Login rate-limiting (brute-force protection) ──────────────────────────
    @app.before_request
    def check_login_rate_limit():
        if request.path == "/login" and request.method == "POST":
            ip = request.remote_addr or "unknown"
            limited = _is_rate_limited(
                ip,
                app.config["LOGIN_MAX_ATTEMPTS"],
                app.config["LOGIN_LOCKOUT_SECS"],
            )
            if limited:
                mins = app.config["LOGIN_LOCKOUT_SECS"] // 60
                return jsonify({
                    "error": f"Too many login attempts. Please try again in {mins} minute(s)."
                }), 429

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(approvals_bp)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # debug=False in production; read from env
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
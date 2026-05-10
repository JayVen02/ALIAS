import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = os.getenv("MYSQL_DB")
    MYSQL_CURSORCLASS = "DictCursor"

    UPLOAD_FOLDER = os.path.join("static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload cap

    # ── Session / Cookie hardening ──────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Enable only under HTTPS in production
    SESSION_COOKIE_SECURE = (
        os.getenv("HTTPS_ENABLED", "false").lower() == "true"
    )

    # Session expires 1 hour after last activity.
    # NOTE: Browsers display cookie expiration in UTC (8 hours behind PH time).
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_REFRESH_EACH_REQUEST = True

    # ── Login rate-limit window ─────────────────────
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_SECS = int(os.getenv("LOGIN_LOCKOUT_SECS", "300"))
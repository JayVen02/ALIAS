import os
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
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit for uploads nii

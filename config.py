import os

class Config:
    MYSQL_HOST     = 'localhost'
    MYSQL_PORT     = 3306
    MYSQL_USER     = 'root'
    MYSQL_PASSWORD = '12345'
    MYSQL_DB       = 'alias_db'

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'alias-secret-key')

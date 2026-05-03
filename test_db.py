from app import create_app
from extensions import mysql

app = create_app()
with app.app_context():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categories LIMIT 1")
    print("CATEGORIES:", cur.fetchall())
    cur.execute("SELECT * FROM subcategories LIMIT 1")
    print("SUBCATEGORIES:", cur.fetchall())

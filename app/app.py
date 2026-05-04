from flask import Flask, render_template
import mysql.connector
import os
import time

app = Flask(__name__)

def get_db_connection():
    time.sleep(5)
    return mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST'),
        user=os.environ.get('MYSQL_USER'),
        password=os.environ.get('MYSQL_PASSWORD'),
        database=os.environ.get('MYSQL_DB')
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    return render_template('index.html')

@app.route('/audit')
def audit():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('index.html')

@app.route('/test-db')
def test_db():
    try:
        db = get_db_connection()
        db.close()
        return "The ALIAS Web Server and MySQL Database are connected successfully!"
    except Exception as e:
        return f"Web server is running, but database connection failed: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
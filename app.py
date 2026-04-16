from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secretkey123'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'alias_db'

mysql = MySQL(app)


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user and user[2] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash("Login failed. Wrong username or password.")
            return redirect(url_for('login'))

    return render_template('login.html')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- HOME ----------------
@app.route('/')
def home():
    if 'logged_in' in session:
        return render_template('index.html')
    return redirect(url_for('login'))


@app.route('/inventory')
def inventory():
    if 'logged_in' in session:
        return render_template('index.html')
    return redirect(url_for('login'))


@app.route('/audit')
def audit():
    if 'logged_in' in session:
        return render_template('index.html')
    return redirect(url_for('login'))


@app.route('/history')
def history():
    if 'logged_in' in session:
        return render_template('index.html')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
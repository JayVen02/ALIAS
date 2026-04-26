import os, datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash
from functools import wraps

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)




# ---------------- DECORATORS ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s OR username=%s", (email, email))
        user = cur.fetchone()

        if user:
            if user['password'] == password:
                session.clear()
                session['logged_in'] = True
                session['email'] = email
                session['username'] = user.get('username', email)
                session['full_name'] = user.get('full_name') if user.get('full_name') else user.get('username', email)
                session['user_id'] = user['id']
                session['role'] = user.get('role', 'staff')
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect password. Please try again.")
        else:
            flash("Incorrect email address. User not found.")
        
        return redirect(url_for('login'))

    return render_template('login.html')


# ---------------- LOGOUT ----------------
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- HOME ----------------
@app.route('/audit/<category_name>/download-pdf', methods=['POST'])
@login_required
def download_pdf(category_name):
    from pdf_generator import generate_physical_count_pdf
    form = request.form

    as_of_date         = form.get('as_of_date', datetime.date.today().strftime('%B %d, %Y'))
    accountable_person = form.get('accountable_person', '')
    position           = form.get('position', '')
    department         = form.get('department', '')

    articles   = form.getlist('pdf_article[]')
    descs      = form.getlist('pdf_desc[]')
    prop_nos   = form.getlist('pdf_propno[]')
    units      = form.getlist('pdf_unit[]')
    unit_vals  = form.getlist('pdf_unitval[]')
    qty_cards  = form.getlist('pdf_qtycard[]')
    qty_phys   = form.getlist('pdf_qtyphys[]')
    remarks_l  = form.getlist('pdf_remarks[]')

    items = []
    for i in range(len(articles)):
        items.append({
            'article':     articles[i]   if i < len(articles)  else '',
            'description': descs[i]      if i < len(descs)     else '',
            'property_no': prop_nos[i]   if i < len(prop_nos)  else '',
            'unit_measure': units[i]     if i < len(units)     else '',
            'unit_value':  unit_vals[i]  if i < len(unit_vals) else '',
            'qty_card':    qty_cards[i]  if i < len(qty_cards) else '',
            'qty_physical': qty_phys[i]  if i < len(qty_phys)  else '',
            'remarks':     remarks_l[i]  if i < len(remarks_l) else '',
        })

    pdf_buffer = generate_physical_count_pdf(
        category_name=category_name,
        as_of_date=as_of_date,
        accountable_person=accountable_person,
        position=position,
        department=department,
        items=items
    )

    safe_name = category_name.replace(' ', '_')
    filename  = f"Physical_Count_{safe_name}.pdf"

    response = make_response(pdf_buffer.read())
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@app.route('/api/generate_pdf_monthly')
@login_required
def generate_pdf_monthly():
    from pdf_generator import generate_physical_count_pdf
    category_name = request.args.get('category')
    subcategory_name = request.args.get('subcategory')
    month = int(request.args.get('month', datetime.date.today().month))
    year = int(request.args.get('year', datetime.date.today().year))
    day = request.args.get('day')
    
    # Get accountability info from modal
    accountable_person = request.args.get('person', 'First Middle Last Name')
    position = request.args.get('position', 'Position Title')
    department = request.args.get('dept', 'Department Name')
    certified_by = request.args.get('certified', 'First Middle Last Name')
    certified_role = request.args.get('certified_role', 'Position Title')
    approved_by = request.args.get('approved', 'First Middle Last Name')
    approved_role = request.args.get('approved_role', 'Position Title')

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    cat = cur.fetchone()

    if not cat:
        return "Category not found", 404

    # Build query for LIVE data matching the activity
    query = """
        SELECT i.*, c.name as category_name, s.name as subcategory_name 
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.id
        JOIN subcategories s ON i.subcategory_id = s.id
        WHERE i.category_id = %s 
    """
    params = [cat['id']]

    if subcategory_name:
        query += " AND s.name = %s "
        params.append(subcategory_name)

    if day:
        # Match items created OR updated on that specific day
        query += """ 
            AND (
                (DAY(i.date_created) = %s AND MONTH(i.date_created) = %s AND YEAR(i.date_created) = %s)
                OR 
                (DAY(i.date_updated) = %s AND MONTH(i.date_updated) = %s AND YEAR(i.date_updated) = %s)
            )
        """
        params.extend([int(day), month, year, int(day), month, year])
    else:
        query += """
            AND (
                (MONTH(i.date_created) = %s AND YEAR(i.date_created) = %s)
                OR 
                (MONTH(i.date_updated) = %s AND YEAR(i.date_updated) = %s)
            )
        """
        params.extend([month, year, month, year])
    
    cur.execute(query, tuple(params))
    items = cur.fetchall()

    import calendar
    month_name = calendar.month_name[month]
    as_of_date = f"{month_name} {day + ', ' if day else ''}{year}"

    # Prepare items for PDF generator
    pdf_items = []
    for it in items:
        pdf_items.append({
            'article': it['article'] or it['subcategory_name'],
            'description': it['name'],
            'property_no': it['stock_number'] or '',
            'unit_measure': it['unit_of_measure'] or '',
            'unit_value': it['unit_value'] or 0,
            'qty_card': it['quantity'],
            'qty_physical': it['on_hand_per_count'] or 0,
            'remarks': it['remarks'] or ''
        })

    pdf_buffer = generate_physical_count_pdf(
        category_name=category_name,
        as_of_date=as_of_date,
        accountable_person=accountable_person,
        position=position,
        department=department,
        items=pdf_items,
        certified_by=certified_by,
        certified_role=certified_role,
        approved_by=approved_by,
        approved_role=approved_role
    )

    day_str = f"_{day}" if day else ""
    filename = f"Audit_{category_name.replace(' ', '_')}{day_str}_{month_name}_{year}.pdf"
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ---------------- PAGE ROUTES ----------------
@app.route('/')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT i.*, c.name as category_name, s.name as subcategory_name 
        FROM inventory_items i
        JOIN categories c ON i.category_id = c.id
        JOIN subcategories s ON i.subcategory_id = s.id
        ORDER BY i.date_created DESC, i.id DESC
        LIMIT 10
    """)
    recent_items = cur.fetchall()
    return render_template('index.html', recent_items=recent_items)

@app.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html')

@app.route('/audit')
@login_required
def audit():
    cur = mysql.connection.cursor()
    # Ensure table exists (failsafe)
    cur.execute("SHOW TABLES LIKE 'audit_logs'")
    if not cur.fetchone():
        # Create table without cascade delete to preserve history
        cur.execute("""
            CREATE TABLE audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT NULL,
                user_id INT NOT NULL,
                action_type ENUM('CREATE', 'UPDATE', 'DELETE', 'QUANTITY_ADJUST') NOT NULL,
                old_value TEXT,
                new_value TEXT,
                change_reason VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # Backfill existing items into audit logs
        cur.execute("""
            INSERT INTO audit_logs (item_id, user_id, action_type, new_value, created_at)
            SELECT id, %s, 'CREATE', 'Initial inventory sync', date_created FROM inventory_items
        """, (session.get('user_id') or 1,))
        mysql.connection.commit()

    # Also backfill if table exists but is empty
    cur.execute("SELECT COUNT(*) as count FROM audit_logs")
    if cur.fetchone()['count'] == 0:
        cur.execute("""
            INSERT INTO audit_logs (item_id, user_id, action_type, new_value, created_at)
            SELECT id, %s, 'CREATE', 'Inventory Sync', date_created FROM inventory_items
        """, (session.get('user_id') or 1,))
        mysql.connection.commit()

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    return render_template('audit.html', categories=categories)

@app.route('/audit/<category_name>')
@login_required
def audit_form(category_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    cat = cur.fetchone()
    
    filtered_items = []
    if cat:
        cur.execute("""
            SELECT i.*, c.name as category_name, s.name as subcategory_name 
            FROM inventory_items i
            JOIN categories c ON i.category_id = c.id
            JOIN subcategories s ON i.subcategory_id = s.id
            WHERE i.category_id = %s
        """, (cat['id'],))
        filtered_items = cur.fetchall()
        
    return render_template('audit_form.html', category_name=category_name, items=filtered_items)

@app.route('/audit/history/<category_name>')
@login_required
def audit_category_history(category_name):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            DATE(l.created_at) as audit_date,
            c.name as category_name, 
            s.name as subcategory_name,
            COUNT(*) as activity_count
        FROM audit_logs l
        JOIN inventory_items i ON l.item_id = i.id
        JOIN categories c ON i.category_id = c.id
        JOIN subcategories s ON i.subcategory_id = s.id
        WHERE c.name = %s
        GROUP BY audit_date, category_name, subcategory_name
        ORDER BY audit_date DESC LIMIT 50
    """, (category_name,))
    history = cur.fetchall()
    return render_template('audit_history.html', category_name=category_name, audit_history=history)

@app.route('/history')
@login_required
def history():
    cur = mysql.connection.cursor()
    # Ensure table exists and is populated
    cur.execute("SHOW TABLES LIKE 'audit_logs'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT NULL,
                user_id INT NOT NULL,
                action_type ENUM('CREATE', 'UPDATE', 'DELETE', 'QUANTITY_ADJUST') NOT NULL,
                old_value TEXT,
                new_value TEXT,
                change_reason VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cur.execute("""
            INSERT INTO audit_logs (item_id, user_id, action_type, new_value, created_at)
            SELECT id, %s, 'CREATE', 'Inventory Sync', date_created FROM inventory_items
        """, (session.get('user_id') or 1,))
        mysql.connection.commit()
    
    cur.execute("SELECT COUNT(*) as count FROM audit_logs")
    if cur.fetchone()['count'] == 0:
        cur.execute("""
            INSERT INTO audit_logs (item_id, user_id, action_type, new_value, created_at)
            SELECT id, %s, 'CREATE', 'Inventory Sync', date_created FROM inventory_items
        """, (session.get('user_id') or 1,))
        mysql.connection.commit()

    cur.execute("""
        SELECT l.*, COALESCE(u.full_name, u.username) as officer_name, c.name as category_name
        FROM audit_logs l
        JOIN users u ON l.user_id = u.id
        LEFT JOIN inventory_items i ON l.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        ORDER BY l.created_at DESC LIMIT 50
    """)
    logs = cur.fetchall()
    return render_template('history.html', logs=logs)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        age = request.form.get('age')
        birthdate = request.form.get('birthdate')
        address = request.form.get('address')
        contact = request.form.get('contact')
        skills = request.form.get('skills')
        work = request.form.get('work')
        
        cur.execute("""
            UPDATE users SET 
                full_name=%s, email=%s, age=%s, 
                birthdate=%s, address=%s, contact_number=%s,
                skills=%s, work_experience=%s
            WHERE username=%s
        """, (full_name, email, age, birthdate, address, contact, skills, work, session['username']))
        mysql.connection.commit()
        return redirect(url_for('profile'))

    cur.execute("SELECT * FROM users WHERE username=%s", (session['username'],))
    user = cur.fetchone()
    return render_template('profile.html', user=user)


@app.route('/profile/upload', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'profile_pic' not in request.files:
        return redirect(url_for('profile'))
    
    file = request.files['profile_pic']
    if file.filename == '':
        return redirect(url_for('profile'))

    if file:
        filename = f"profile_{session['username']}.png"
        filepath = os.path.join('static/uploads', filename)
        
        # Ensure directory exists
        os.makedirs('static/uploads', exist_ok=True)
        
        file.save(filepath)
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET profile_picture=%s WHERE username=%s", (filepath, session['username']))
        mysql.connection.commit()
        
    return redirect(url_for('profile'))


# ---------------- INVENTORY API ----------------
@app.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM categories")
        return {"categories": cur.fetchall()}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/subcategories', methods=['GET'])
@login_required
def get_subcategories():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM subcategories")
        return {"subcategories": cur.fetchall()}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/inventory', methods=['GET'])
@login_required
def get_inventory():
    try:
        category_id = request.args.get('category_id')
        subcategory_id = request.args.get('subcategory_id')
        search = request.args.get('search')
        sort = request.args.get('sort', 'latest')

        query = """
            SELECT i.*, c.name as category_name, s.name as subcategory_name 
            FROM inventory_items i
            JOIN categories c ON i.category_id = c.id
            JOIN subcategories s ON i.subcategory_id = s.id
            WHERE 1=1
        """
        params = []
        if category_id:
            query += " AND i.category_id = %s"
            params.append(category_id)
        if subcategory_id:
            query += " AND i.subcategory_id = %s"
            params.append(subcategory_id)
        if search:
            query += " AND (i.name LIKE %s OR i.article LIKE %s OR c.name LIKE %s OR s.name LIKE %s)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        if sort == 'latest':
            query += " ORDER BY i.date_updated DESC"
        elif sort == 'oldest':
            query += " ORDER BY i.date_updated ASC"
        elif sort == 'name':
            query += " ORDER BY i.name ASC"
        elif sort == 'qty_high':
            query += " ORDER BY i.quantity DESC"
        elif sort == 'qty_low':
            query += " ORDER BY i.quantity ASC"

        cur = mysql.connection.cursor()
        cur.execute(query, tuple(params))
        items = cur.fetchall()
        
        # Format dates for JSON
        for item in items:
            if item['date_created']:
                item['date_created'] = item['date_created'].strftime('%m/%d/%Y')
            if item['date_updated']:
                item['date_updated'] = item['date_updated'].strftime('%m/%d/%Y')
            if item['unit_value']:
                item['unit_value'] = float(item['unit_value'])
            if item['overage_value']:
                item['overage_value'] = float(item['overage_value'])

        return {"items": items}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/inventory', methods=['POST'])
@login_required
def create_item():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO inventory_items (category_id, subcategory_id, name, quantity)
        VALUES (%s, %s, %s, %s)
    """, (data['category_id'], data['subcategory_id'], data['name'], data['quantity']))
    mysql.connection.commit()
    new_id = cur.lastrowid
    
    # Audit Log
    cur.execute("INSERT INTO audit_logs (item_id, user_id, action_type, new_value) VALUES (%s, %s, 'CREATE', %s)",
                (new_id, session.get('user_id'), str(data)))
    mysql.connection.commit()
    
    return {"id": new_id}, 201

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    data = request.json
    fields = []
    params = []
    for key, val in data.items():
        if key == 'id': continue
        if key == 'category_name' or key == 'subcategory_name': continue
        fields.append(f"{key} = %s")
        params.append(val)
    
    if not fields:
        return {"error": "No fields to update"}, 400
    
    params.append(item_id)
    cur = mysql.connection.cursor()
    cur.execute(f"UPDATE inventory_items SET {', '.join(fields)}, date_updated = CURDATE() WHERE id = %s", tuple(params))
    
    # Audit Log
    cur.execute("INSERT INTO audit_logs (item_id, user_id, action_type, new_value) VALUES (%s, %s, 'UPDATE', %s)",
                (item_id, session.get('user_id'), str(data)))
    
    mysql.connection.commit()
    return {"message": "Updated"}

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    cur = mysql.connection.cursor()
    # Audit Log before delete
    cur.execute("INSERT INTO audit_logs (item_id, user_id, action_type) VALUES (%s, %s, 'DELETE')",
                (item_id, session.get('user_id')))
    
    cur.execute("DELETE FROM inventory_items WHERE id = %s", (item_id,))
    mysql.connection.commit()
    return {"message": "Deleted"}


# ---------------- USER MANAGEMENT API ----------------
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()
    return {"users": users}

@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not password:
        return {"error": "Username and password are required"}, 400
        
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                    (username, email, password))
        mysql.connection.commit()
        return {"message": "User added successfully"}, 201
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    cur = mysql.connection.cursor()
    try:
        if password:
            cur.execute("UPDATE users SET username=%s, email=%s, password=%s WHERE id=%s", 
                        (username, email, password, user_id))
        else:
            cur.execute("UPDATE users SET username=%s, email=%s WHERE id=%s", 
                        (username, email, user_id))
        mysql.connection.commit()
        return {"message": "User updated successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        mysql.connection.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT"))
    app.run(host='0.0.0.0', port=port, debug=False)
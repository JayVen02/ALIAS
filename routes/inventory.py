from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from models import db, User, Item, History
from werkzeug.security import generate_password_hash, check_password_hash
from pdf_generator import generate_physical_count_pdf
from functools import wraps
import datetime

inventory_bp = Blueprint('inventory', __name__)

# ── HELPERS ───────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('inventory.login'))
        return f(*args, **kwargs)
    return decorated

def log_history(action_text):
    if 'user_id' in session:
        db.session.add(History(user_id=session['user_id'], action=action_text))

# ── AUTH ──────────────────────────────────────────────────────────────────────

@inventory_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('inventory.home'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('inventory.login'))
        if not user.is_active:
            flash('Account deactivated. Contact admin.', 'error')
            return redirect(url_for('inventory.login'))
        session['user_id']   = user.id
        session['username']  = user.username
        session['full_name'] = user.full_name
        session['role']      = user.role
        return redirect(url_for('inventory.home'))
    return render_template('login.html')

@inventory_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inventory.login'))

# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@inventory_bp.route('/')
@login_required
def home():
    recent_items = Item.query.filter_by(is_deleted=False)\
                      .order_by(Item.updated_at.desc()).limit(10).all()
    emergency_qty  = db.session.query(db.func.sum(Item.system_qty))\
                       .filter_by(subcategory='EMERGENCY',  is_deleted=False).scalar() or 0
    medical_qty    = db.session.query(db.func.sum(Item.system_qty))\
                       .filter_by(subcategory='MEDICAL',    is_deleted=False).scalar() or 0
    veterinary_qty = db.session.query(db.func.sum(Item.system_qty))\
                       .filter_by(subcategory='VETERINARY', is_deleted=False).scalar() or 0
    return render_template('index.html',
        recent_items=recent_items,
        emergency_qty=emergency_qty,
        medical_qty=medical_qty,
        veterinary_qty=veterinary_qty
    )

# ── INVENTORY ─────────────────────────────────────────────────────────────────

@inventory_bp.route('/inventory')
@login_required
def inventory():
    category = request.args.get('category', 'SUPPLY')
    search   = request.args.get('search', '')
    sort     = request.args.get('sort', 'latest')
    query = Item.query.filter_by(is_deleted=False, category=category)
    if search:
        query = query.filter(Item.name.ilike(f'%{search}%'))
    query = query.order_by(Item.updated_at.desc() if sort == 'latest' else Item.name.asc())
    items = query.all()
    return render_template('inventory.html', items=items, category=category, search=search, sort=sort)

@inventory_bp.route('/inventory/add', methods=['POST'])
@login_required
def add_item():
    category    = request.form.get('category', 'SUPPLY')
    subcategory = request.form.get('subcategory', '').upper()
    name        = request.form.get('name', '').strip().upper()
    quantity    = request.form.get('quantity', type=int, default=0)
    if not name or not subcategory:
        flash('Name and subcategory are required.', 'error')
        return redirect(url_for('inventory.inventory', category=category))
    last = Item.query.order_by(Item.id.desc()).first()
    next_id   = (last.id + 1) if last else 1
    item_code = f"GSO-{category[:3]}-{str(next_id).zfill(4)}"
    item = Item(item_code=item_code, category=category, subcategory=subcategory,
                name=name, system_qty=quantity, created_by=session['user_id'])
    db.session.add(item)
    db.session.flush()
    log_history(f"Added {quantity} (+{quantity}) in {subcategory} {name}.")
    db.session.commit()
    flash(f'{name} added successfully.', 'success')
    return redirect(url_for('inventory.inventory', category=category))

@inventory_bp.route('/inventory/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_item(item_id):
    item     = Item.query.get_or_404(item_id)
    old_qty  = item.system_qty
    new_qty  = request.form.get('quantity', type=int, default=item.system_qty)
    new_name = request.form.get('name', item.name).strip().upper()
    new_sub  = request.form.get('subcategory', item.subcategory).upper()
    diff     = new_qty - old_qty
    item.name        = new_name
    item.subcategory = new_sub
    item.system_qty  = new_qty
    sign = f'+{diff}' if diff > 0 else str(diff)
    log_history(
        f"{'Added' if diff > 0 else 'Removed'} {abs(diff)} ({sign}) in {new_sub} {new_name}."
        if diff != 0 else f"Edited item {new_name} in {new_sub}."
    )
    db.session.commit()
    flash(f'{new_name} updated.', 'success')
    return redirect(url_for('inventory.inventory', category=item.category))

@inventory_bp.route('/inventory/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    item.is_deleted = True
    log_history(f"Deleted item {item.name} from {item.subcategory}.")
    db.session.commit()
    flash(f'{item.name} removed.', 'info')
    return redirect(url_for('inventory.inventory', category=item.category))

# ── AUDIT ─────────────────────────────────────────────────────────────────────

AUDIT_CATEGORIES = [
    {'name': 'Fuel Consumption',                  'icon': '⛽'},
    {'name': 'Transport Vehicle',                 'icon': '🚑'},
    {'name': 'Medicines',                         'icon': '💊'},
    {'name': 'Emergency Supplies',                'icon': '🔦'},
    {'name': 'Property, Plant and Equipment ICT', 'icon': '🖥'},
]

CATEGORY_MAP = {
    'Fuel Consumption':                  ('VEHICLE', 'FUEL'),
    'Transport Vehicle':                 ('VEHICLE', 'VEHICLE'),
    'Medicines':                         ('SUPPLY',  'MEDICAL'),
    'Emergency Supplies':                ('SUPPLY',  'EMERGENCY'),
    'Property, Plant and Equipment ICT': ('SUPPLY',  'VETERINARY'),
}

@inventory_bp.route('/audit')
@login_required
def audit_categories():
    return render_template('audit_categories.html', categories=AUDIT_CATEGORIES)

@inventory_bp.route('/audit/<category_name>', methods=['GET', 'POST'])
@login_required
def audit_form(category_name):
    cat_tuple = CATEGORY_MAP.get(category_name)
    if cat_tuple:
        cat, sub = cat_tuple
        db_items = Item.query.filter_by(is_deleted=False, category=cat, subcategory=sub).all()
        filtered_items = [
            {'id': i.item_code, 'category': category_name,
             'name': i.name, 'system_qty': i.system_qty}
            for i in db_items
        ]
    else:
        filtered_items = []
    if request.method == 'POST':
        return render_template('audit_form.html', category_name=category_name,
                               items=filtered_items, success=True)
    return render_template('audit_form.html', category_name=category_name, items=filtered_items)

@inventory_bp.route('/audit/<category_name>/download-pdf', methods=['POST'])
@login_required
def download_pdf(category_name):
    form               = request.form
    as_of_date         = form.get('as_of_date', datetime.date.today().strftime('%B %d, %Y'))
    accountable_person = form.get('accountable_person', 'DOLLYN JEAN A. SABELLINA')
    position           = form.get('position', 'MUNICIPAL ACCOUNTANT')
    department         = form.get('department', 'ACCOUNTING')
    articles  = form.getlist('pdf_article[]')
    descs     = form.getlist('pdf_desc[]')
    prop_nos  = form.getlist('pdf_propno[]')
    units     = form.getlist('pdf_unit[]')
    unit_vals = form.getlist('pdf_unitval[]')
    qty_cards = form.getlist('pdf_qtycard[]')
    qty_phys  = form.getlist('pdf_qtyphys[]')
    remarks_l = form.getlist('pdf_remarks[]')
    items = []
    for i in range(len(articles)):
        items.append({
            'article':      articles[i]   if i < len(articles)  else '',
            'description':  descs[i]      if i < len(descs)     else '',
            'property_no':  prop_nos[i]   if i < len(prop_nos)  else '',
            'unit_measure': units[i]      if i < len(units)     else '',
            'unit_value':   unit_vals[i]  if i < len(unit_vals) else '',
            'qty_card':     qty_cards[i]  if i < len(qty_cards) else '',
            'qty_physical': qty_phys[i]   if i < len(qty_phys)  else '',
            'remarks':      remarks_l[i]  if i < len(remarks_l) else '',
        })
    pdf_buffer = generate_physical_count_pdf(
        category_name=category_name, as_of_date=as_of_date,
        accountable_person=accountable_person, position=position,
        department=department, items=items
    )
    safe_name = category_name.replace(' ', '_')
    response  = make_response(pdf_buffer.read())
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="Physical_Count_{safe_name}.pdf"'
    return response

# ── HISTORY ───────────────────────────────────────────────────────────────────

@inventory_bp.route('/history')
@login_required
def history():
    logs = History.query.order_by(History.timestamp.desc()).all()
    return render_template('history.html', logs=logs)

# ── SEED ──────────────────────────────────────────────────────────────────────

@inventory_bp.route('/seed')
def seed():
    db.create_all()
    if User.query.filter_by(username='admin').first():
        return "Already seeded. <a href='/login'>Login</a>"
    admin = User(username='admin', password_hash=generate_password_hash('admin123'),
                 full_name='GSO Admin', role='admin')
    staff = User(username='staff', password_hash=generate_password_hash('staff123'),
                 full_name='Inventory Staff', role='inventory_staff')
    db.session.add_all([admin, staff])
    db.session.flush()
    sample = [
        Item(item_code='GSO-SUP-0001', category='SUPPLY', subcategory='EMERGENCY',  name='COFFEE',                            system_qty=2,  created_by=admin.id),
        Item(item_code='GSO-SUP-0002', category='SUPPLY', subcategory='EMERGENCY',  name='COMMERCIAL RICE',                   system_qty=12, created_by=admin.id),
        Item(item_code='GSO-SUP-0003', category='SUPPLY', subcategory='EMERGENCY',  name='CANNED (SARDINES)',                 system_qty=32, created_by=admin.id),
        Item(item_code='GSO-SUP-0004', category='SUPPLY', subcategory='EMERGENCY',  name='CANNED (CORNED BEEF)',              system_qty=25, created_by=admin.id),
        Item(item_code='GSO-SUP-0005', category='SUPPLY', subcategory='VETERINARY', name='VIT. B COMPLEX WITH LIVER EXTRACT', system_qty=12, created_by=admin.id),
        Item(item_code='GSO-SUP-0006', category='SUPPLY', subcategory='VETERINARY', name='ALNENDAZOLE DEWORMER (VALBAZINE)',  system_qty=24, created_by=admin.id),
        Item(item_code='GSO-SUP-0007', category='SUPPLY', subcategory='MEDICAL',    name='DISPOSABLE SYRINGE 3ML',            system_qty=27, created_by=admin.id),
        Item(item_code='GSO-VEH-0008', category='VEHICLE', subcategory='VEHICLE',   name='ISUZU VAN NHR CANTER',              system_qty=1,  created_by=admin.id),
        Item(item_code='GSO-VEH-0009', category='VEHICLE', subcategory='VEHICLE',   name='MEEDO BONGGO VEHICLE',              system_qty=1,  created_by=admin.id),
        Item(item_code='GSO-VEH-0010', category='VEHICLE', subcategory='VEHICLE',   name='MDRR RESCUE VEHICLE L300',          system_qty=1,  created_by=admin.id),
    ]
    db.session.add_all(sample)
    history_entries = [
        History(user_id=admin.id, action='Added 1 (+1) in Emergency Coffee.',                timestamp=datetime.datetime(2025,5,17,15,41)),
        History(user_id=admin.id, action='Added 5 (+5) in Emergency Commercial Rice.',        timestamp=datetime.datetime(2025,5,29,13,55)),
        History(user_id=admin.id, action='Removed 2 (-2) in Emergency Canned (Sardines).',    timestamp=datetime.datetime(2025,5,29,13,55)),
        History(user_id=admin.id, action='Added 10 (+10) in Emergency Canned (Corned Beef).', timestamp=datetime.datetime(2025,5,29,14,1)),
        History(user_id=admin.id, action='Added 7 (+7) in Medical Disposable Syringe 3ML.',  timestamp=datetime.datetime(2025,5,29,16,30)),
    ]
    db.session.add_all(history_entries)
    db.session.commit()
    return "Seeded! <a href='/login'>Login</a> — admin/admin123 or staff/staff123"

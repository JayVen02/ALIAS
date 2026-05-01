SORT_MAP = {
    "latest": "i.date_updated DESC",
    "oldest": "i.date_updated ASC",
    "name": "i.name ASC",
    "qty_high": "i.quantity DESC",
    "qty_low": "i.quantity ASC",
}

ITEM_SELECT = """
    SELECT i.*, c.name AS category_name, s.name AS subcategory_name
    FROM inventory_items i
    JOIN categories c ON i.category_id = c.id
    JOIN subcategories s ON i.subcategory_id = s.id
"""

# ── Read ──────────────────────────────────────────────────────────────────────

def get_all_categories(db):
    cur = db.connection.cursor()
    cur.execute("SELECT * FROM categories")
    return cur.fetchall()


def get_all_subcategories(db):
    cur = db.connection.cursor()
    cur.execute("SELECT * FROM subcategories")
    return cur.fetchall()


def get_items(db, category_id=None, subcategory_id=None, search=None, sort="latest"):
    query = ITEM_SELECT + " WHERE 1=1"
    params = []

    if category_id:
        query += " AND i.category_id = %s"
        params.append(category_id)
    if subcategory_id:
        query += " AND i.subcategory_id = %s"
        params.append(subcategory_id)
    if search:
        query += " AND (i.name LIKE %s OR i.article LIKE %s OR c.name LIKE %s OR s.name LIKE %s)"
        like = f"%{search}%"
        params.extend([like, like, like, like])

    order = SORT_MAP.get(sort, SORT_MAP["latest"])
    query += f" ORDER BY {order}"

    cur = db.connection.cursor()
    cur.execute(query, tuple(params))
    return cur.fetchall()


def get_recent_items(db, limit=10):
    cur = db.connection.cursor()
    cur.execute(
        ITEM_SELECT + " ORDER BY i.date_created DESC, i.id DESC LIMIT %s",
        (limit,),
    )
    return cur.fetchall()


def get_items_by_category_name(db, category_name):
    cur = db.connection.cursor()
    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    cat = cur.fetchone()
    if not cat:
        return None, []

    cur.execute(ITEM_SELECT + " WHERE i.category_id = %s", (cat["id"],))
    return cat, cur.fetchall()


def get_item_by_details(db, category_id, subcategory_id, name):
    """Check if item with same category, subcategory, and name exists."""
    cur = db.connection.cursor()
    cur.execute(
        "SELECT * FROM inventory_items WHERE category_id = %s AND subcategory_id = %s AND name = %s LIMIT 1",
        (category_id, subcategory_id, name),
    )
    return cur.fetchone()


# ── Write ─────────────────────────────────────────────────────────────────────

def create_item(db, category_id, subcategory_id, name, quantity):
    cur = db.connection.cursor()
    cur.execute(
        "INSERT INTO inventory_items (category_id, subcategory_id, name, quantity) VALUES (%s, %s, %s, %s)",
        (category_id, subcategory_id, name, quantity),
    )
    return cur.lastrowid


def add_quantity_to_item(db, item_id, quantity_to_add):
    """Add quantity to an existing item and return the updated quantity."""
    cur = db.connection.cursor()
    cur.execute(
        "UPDATE inventory_items SET quantity = quantity + %s, date_updated = CURDATE() WHERE id = %s",
        (quantity_to_add, item_id),
    )
    # Get the updated item
    cur.execute("SELECT quantity FROM inventory_items WHERE id = %s", (item_id,))
    result = cur.fetchone()
    return result["quantity"] if result else None


_EXCLUDED_KEYS = {"id", "category_name", "subcategory_name"}


def update_item(db, item_id, data):
    fields = [(k, v) for k, v in data.items() if k not in _EXCLUDED_KEYS]
    if not fields:
        return False

    set_clause = ", ".join(f"{k} = %s" for k, _ in fields)
    values = [v for _, v in fields] + [item_id]

    cur = db.connection.cursor()
    cur.execute(
        f"UPDATE inventory_items SET {set_clause}, date_updated = CURDATE() WHERE id = %s",
        tuple(values),
    )
    return True


def delete_item(db, item_id):
    cur = db.connection.cursor()
    cur.execute("DELETE FROM inventory_items WHERE id = %s", (item_id,))


# ── Serialization helper ──────────────────────────────────────────────────────

def serialize_item(item):
    """Convert date/decimal fields so they are JSON-serialisable."""
    result = dict(item)
    if result.get("date_created"):
        result["date_created"] = result["date_created"].strftime("%m/%d/%Y")
    if result.get("date_updated"):
        result["date_updated"] = result["date_updated"].strftime("%m/%d/%Y")
    if result.get("unit_value") is not None:
        result["unit_value"] = float(result["unit_value"])
    if result.get("overage_value") is not None:
        result["overage_value"] = float(result["overage_value"])
    return result

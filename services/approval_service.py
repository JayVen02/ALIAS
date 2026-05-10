"""
approval_service.py
Handles creation, retrieval, approval, and rejection of pending inventory
change requests submitted by staff/member users.
"""

CREATE_REQUESTS_TABLE = """
    CREATE TABLE IF NOT EXISTS inventory_change_requests (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        item_id       INT NULL COMMENT 'NULL for CREATE actions',
        requested_by  INT NOT NULL,
        action_type   ENUM('CREATE', 'UPDATE', 'DELETE') NOT NULL,
        payload       TEXT NOT NULL COMMENT 'JSON-serialised change data',
        reason        VARCHAR(500) DEFAULT NULL,
        status        ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
        reviewed_by   INT NULL,
        review_note   VARCHAR(500) DEFAULT NULL,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_at   TIMESTAMP NULL,
        FOREIGN KEY (requested_by) REFERENCES users(id),
        FOREIGN KEY (reviewed_by)  REFERENCES users(id)
    )
"""


def ensure_requests_table(db):
    """Create the table if it does not yet exist."""
    cur = db.connection.cursor()
    cur.execute(CREATE_REQUESTS_TABLE)
    db.connection.commit()


# ── Submit ────────────────────────────────────────────────────────────────────

def submit_request(db, item_id, requested_by, action_type, payload, reason=None):
    """Insert a new pending change request; returns the new row id."""
    import json
    cur = db.connection.cursor()
    cur.execute(
        """INSERT INTO inventory_change_requests
               (item_id, requested_by, action_type, payload, reason)
           VALUES (%s, %s, %s, %s, %s)""",
        (item_id, requested_by, action_type,
         json.dumps(payload) if not isinstance(payload, str) else payload,
         reason),
    )
    db.connection.commit()
    return cur.lastrowid


# ── Read ──────────────────────────────────────────────────────────────────────

def get_pending_requests(db):
    """Return all pending requests, newest first, with requester name."""
    cur = db.connection.cursor()
    cur.execute(
        """SELECT r.*,
                  COALESCE(u.full_name, u.email) AS requester_name,
                  i.name AS item_name
           FROM   inventory_change_requests r
           JOIN   users u ON r.requested_by = u.id
           LEFT JOIN inventory_items i ON r.item_id = i.id
           WHERE  r.status = 'pending'
           ORDER  BY r.created_at DESC""",
    )
    return cur.fetchall()


def get_all_requests(db, limit=100):
    """Return all requests (any status), newest first."""
    cur = db.connection.cursor()
    cur.execute(
        """SELECT r.*,
                  COALESCE(u.full_name, u.email)  AS requester_name,
                  COALESCE(rv.full_name, rv.email) AS reviewer_name,
                  i.name AS item_name
           FROM   inventory_change_requests r
           JOIN   users u  ON r.requested_by = u.id
           LEFT JOIN users rv ON r.reviewed_by = rv.id
           LEFT JOIN inventory_items i ON r.item_id = i.id
           ORDER  BY r.created_at DESC
           LIMIT  %s""",
        (limit,),
    )
    return cur.fetchall()


def get_request_by_id(db, request_id):
    """Return a single request row or None."""
    cur = db.connection.cursor()
    cur.execute(
        """SELECT r.*,
                  COALESCE(u.full_name, u.email) AS requester_name,
                  i.name AS item_name
           FROM   inventory_change_requests r
           JOIN   users u ON r.requested_by = u.id
           LEFT JOIN inventory_items i ON r.item_id = i.id
           WHERE  r.id = %s""",
        (request_id,),
    )
    return cur.fetchone()


def count_pending(db):
    """Return the integer count of pending requests."""
    cur = db.connection.cursor()
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM inventory_change_requests WHERE status = 'pending'"
    )
    row = cur.fetchone()
    return row["cnt"] if row else 0


# ── Review ────────────────────────────────────────────────────────────────────

def approve_request(db, request_id, reviewed_by, review_note=None):
    """Mark request as approved."""
    cur = db.connection.cursor()
    cur.execute(
        """UPDATE inventory_change_requests
           SET status = 'approved', reviewed_by = %s, review_note = %s,
               reviewed_at = CURRENT_TIMESTAMP
           WHERE id = %s AND status = 'pending'""",
        (reviewed_by, review_note, request_id),
    )
    db.connection.commit()
    return cur.rowcount > 0


def reject_request(db, request_id, reviewed_by, review_note=None):
    """Mark request as rejected."""
    cur = db.connection.cursor()
    cur.execute(
        """UPDATE inventory_change_requests
           SET status = 'rejected', reviewed_by = %s, review_note = %s,
               reviewed_at = CURRENT_TIMESTAMP
           WHERE id = %s AND status = 'pending'""",
        (reviewed_by, review_note, request_id),
    )
    db.connection.commit()
    return cur.rowcount > 0

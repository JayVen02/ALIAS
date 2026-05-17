from werkzeug.security import generate_password_hash, check_password_hash


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password using pbkdf2:sha256."""
    return generate_password_hash(plain, method="pbkdf2:sha256", salt_length=16)


def verify_password(stored: str, plain: str) -> bool:
    """
    Check password supporting both hashed AND legacy plaintext (migration path).
    Once an account logs in or changes password it will be re-hashed automatically.
    """
    if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
        return check_password_hash(stored, plain)
    # Legacy plaintext — allows existing seeded accounts to log in
    return stored == plain


# ── Read ──────────────────────────────────────────────────────────────────────

def get_all_users(db):
    cur = db.connection.cursor()
    cur.execute(
        "SELECT id, email, full_name, role, created_at FROM users ORDER BY created_at DESC"
    )
    users = cur.fetchall()
    for user in users:
        if user.get("created_at"):
            user["created_at"] = user["created_at"].strftime("%m/%d/%Y")
    return users


def get_user_by_email(db, email):
    cur = db.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    return cur.fetchone()


def get_user_by_login(db, email):
    """Look up a user by email."""
    cur = db.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    return cur.fetchone()


# ── Write ─────────────────────────────────────────────────────────────────────

def create_user(db, email, password, full_name, role):
    cur = db.connection.cursor()
    hashed = hash_password(password)
    cur.execute(
        "INSERT INTO users (email, password, full_name, role) VALUES (%s, %s, %s, %s)",
        (email, hashed, full_name, role),
    )
    return cur.lastrowid


def update_user(db, user_id, email, full_name, role, password=None):
    cur = db.connection.cursor()
    if password:
        hashed = hash_password(password)
        cur.execute(
            "UPDATE users SET email=%s, password=%s, full_name=%s, role=%s WHERE id=%s",
            (email, hashed, full_name, role, user_id),
        )
    else:
        cur.execute(
            "UPDATE users SET email=%s, full_name=%s, role=%s WHERE id=%s",
            (email, full_name, role, user_id),
        )


def delete_user(db, user_id):
    cur = db.connection.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))


def update_profile(db, email_identifier, full_name, email, age, birthdate,
                   address, contact, skills, work):
    # Sanitize / cap text lengths before storing
    def _cap(val, limit):
        return str(val or "")[:limit]

    # Handle age as integer safely
    try:
        clean_age = int(age) if age and str(age).strip() else None
    except (ValueError, TypeError):
        clean_age = None

    cur = db.connection.cursor()
    cur.execute(
        """UPDATE users SET
               full_name=%s, email=%s, age=%s,
               birthdate=%s, address=%s, contact_number=%s,
               skills=%s, work_experience=%s
           WHERE email=%s""",
        (
            _cap(full_name, 50),
            _cap(email, 50),
            clean_age,
            birthdate or None,
            _cap(address, 255),
            _cap(contact, 20),
            _cap(skills, 500),
            _cap(work, 1000),
            email_identifier,
        ),
    )


def update_profile_picture(db, email, filepath):
    cur = db.connection.cursor()
    cur.execute(
        "UPDATE users SET profile_picture=%s WHERE email=%s",
        (filepath, email),
    )


# ── Validation ────────────────────────────────────────────────────────────────

VALID_ROLES = {"admin", "staff"}
REQUIRED_EMAIL_DOMAIN = "@gso.gov.ph"


def validate_user_payload(email, password=None, confirm_password=None, require_password=True):
    """Return an error string or None if valid."""
    if not email or not email.endswith(REQUIRED_EMAIL_DOMAIN):
        return f"A valid {REQUIRED_EMAIL_DOMAIN} email address is required."
    if len(email) > 254:
        return "Email address is too long."
    if require_password:
        if not password:
            return "Password is required."
        if len(password) < 8:
            return "Password must be at least 8 characters."
        if confirm_password is not None and password != confirm_password:
            return "Passwords do not match."
    elif password and len(password) < 8:
        return "Password must be at least 8 characters."
    return None

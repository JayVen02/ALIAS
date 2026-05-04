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


def create_user(db, email, password, full_name, role):
    cur = db.connection.cursor()
    cur.execute(
        "INSERT INTO users (email, password, full_name, role) VALUES (%s, %s, %s, %s)",
        (email, password, full_name, role),
    )
    return cur.lastrowid


def update_user(db, user_id, email, full_name, role, password=None):
    cur = db.connection.cursor()
    if password:
        cur.execute(
            "UPDATE users SET email=%s, password=%s, full_name=%s, role=%s WHERE id=%s",
            (email, password, full_name, role, user_id),
        )
    else:
        cur.execute(
            "UPDATE users SET email=%s, full_name=%s, role=%s WHERE id=%s",
            (email, full_name, role, user_id),
        )


def delete_user(db, user_id):
    cur = db.connection.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))


def update_profile(db, email_identifier, full_name, email, age, birthdate, address, contact, skills, work):
    cur = db.connection.cursor()
    cur.execute(
        """UPDATE users SET
               full_name=%s, email=%s, age=%s,
               birthdate=%s, address=%s, contact_number=%s,
               skills=%s, work_experience=%s
           WHERE email=%s""",
        (full_name, email, age, birthdate, address, contact, skills, work, email_identifier),
    )


def update_profile_picture(db, email, filepath):
    cur = db.connection.cursor()
    cur.execute(
        "UPDATE users SET profile_picture=%s WHERE email=%s",
        (filepath, email),
    )


VALID_ROLES = {"admin", "staff"}
REQUIRED_EMAIL_DOMAIN = "@gso.gov.ph"


def validate_user_payload(email, password=None, confirm_password=None, require_password=True):
    """Return an error string or None if valid."""
    if not email or not email.endswith(REQUIRED_EMAIL_DOMAIN):
        return f"A valid {REQUIRED_EMAIL_DOMAIN} email address is required."
    if require_password:
        if not password:
            return "Password is required."
        if len(password) < 6:
            return "Password must be at least 6 characters."
        if confirm_password is not None and password != confirm_password:
            return "Passwords do not match."
    elif password and len(password) < 6:
        return "Password must be at least 6 characters."
    return None

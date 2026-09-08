import sqlite3
import os
import hashlib
import secrets


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_PATH = os.path.join(
    BASE_DIR,
    "database",
    "aura.db"
)


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():

    return sqlite3.connect(
        DB_PATH
    )


# --------------------------------------------------
# CREATE USERS TABLE
# --------------------------------------------------

def create_users_table():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


# --------------------------------------------------
# HASH PASSWORD
# --------------------------------------------------

def hash_password(password: str, salt: str = None):

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return f"{salt}${password_hash}"


# --------------------------------------------------
# VERIFY PASSWORD
# --------------------------------------------------

def verify_password(
    password: str,
    stored_password: str
):

    try:

        salt, stored_hash = stored_password.split(
            "$",
            1
        )

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

        return secrets.compare_digest(
            password_hash,
            stored_hash
        )

    except Exception:

        return False


# --------------------------------------------------
# REGISTER USER
# --------------------------------------------------

def register_user(
    username: str,
    email: str,
    password: str
):

    create_users_table()

    connection = get_connection()

    cursor = connection.cursor()

    password_hash = hash_password(
        password
    )

    try:

        cursor.execute("""
            INSERT INTO users
            (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (
            username,
            email,
            password_hash
        ))

        connection.commit()

        user_id = cursor.lastrowid

        return {
            "success": True,
            "user_id": user_id,
            "message": "User registered successfully."
        }

    except sqlite3.IntegrityError:

        return {
            "success": False,
            "message": "Username or email already exists."
        }

    finally:

        connection.close()


# --------------------------------------------------
# LOGIN USER
# --------------------------------------------------

def login_user(
    email: str,
    password: str
):

    create_users_table()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            email,
            password_hash
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    connection.close()

    if not user:

        return {
            "success": False,
            "message": "Invalid email or password."
        }

    user_id = user[0]
    username = user[1]
    user_email = user[2]
    stored_password = user[3]

    if not verify_password(
        password,
        stored_password
    ):

        return {
            "success": False,
            "message": "Invalid email or password."
        }

    return {
        "success": True,
        "user_id": user_id,
        "username": username,
        "email": user_email,
        "message": "Login successful."
    }


# --------------------------------------------------
# GET USER
# --------------------------------------------------

def get_user_by_id(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            email,
            created_at
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    connection.close()

    if not user:
        return None

    return {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "created_at": user[3]
    }
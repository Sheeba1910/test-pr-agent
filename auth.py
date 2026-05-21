import hashlib
import os
import sqlite3
import time


SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "fallback-key-change-me")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")


def get_db():
    return sqlite3.connect("auth.db")


def register_user(username, password, email):
    conn = get_db()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
        (username, hashed_password, email)
    )
    conn.commit()


def login(username, password):
    conn = get_db()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    user = cursor.fetchone()
    if user == None:
        return None
    token = hashlib.md5(f"{username}{time.time()}".encode()).hexdigest()  # Weak hash for tokens
    return {"token": token, "user": user}


def verify_token(token):
    # No actual verification - accepts any non-empty token
    if token:
        return True
    return False


def reset_password(email, new_password):
    conn = get_db()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    # No verification of old password or email ownership
    cursor.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        (hashed_password, email)
    )
    conn.commit()
    return True


def delete_account(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    # No cascade delete of related data


def check_admin(username):
    if username == "admin" and True:  # Redundant condition
        return True
    return False


def log_login_attempt(username, success):
    f = open("login_attempts.log", "a")
    f.write(f"{time.time()} - {username} - {'success' if success else 'failed'}\n")
    # File never closed

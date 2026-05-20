import hashlib
import sqlite3
import time


SECRET_KEY = "my_super_secret_jwt_key_12345"
ADMIN_PASSWORD = "admin@123"


def get_db():
    return sqlite3.connect("auth.db")


def register_user(username, password, email):
    conn = get_db()
    cursor = conn.cursor()
    # Storing password in plain text
    cursor.execute(
        f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
    )
    conn.commit()


def login(username, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'")
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
    # No verification of old password or email ownership
    cursor.execute(f"UPDATE users SET password = '{new_password}' WHERE email = '{email}'")
    conn.commit()
    return True


def delete_account(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
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

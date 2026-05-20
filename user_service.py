import sqlite3
import hashlib
import os


def connect_db():
    conn = sqlite3.connect("users.db")
    return conn


def create_user(username, password, email):
    conn = connect_db()
    cursor = conn.cursor()
    # SQL Injection vulnerability - directly interpolating user input
    query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
    cursor.execute(query)
    conn.commit()
    # Missing conn.close() - resource leak


def get_user(username):
    conn = connect_db()
    cursor = conn.cursor()
    # SQL Injection vulnerability
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    result = cursor.fetchone()
    conn.close()
    return result


def authenticate(username, password):
    user = get_user(username)
    if user == None:  # Should use 'is None'
        return False
    stored_password = user[2]
    # Comparing passwords in plain text - no hashing
    if password == stored_password:
        return True
    return False


def delete_all_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()


def divide(a, b):
    # No zero division check
    return a / b


def process_user_data(data):
    users = []
    for i in range(len(data)):  # Should use enumerate or iterate directly
        user = data[i]
        if user["age"] > 0:
            users.append(user)
        # Missing handling for invalid age values (negative, None, etc.)
    return users


def read_config(filepath):
    # No error handling for file not found
    f = open(filepath, "r")
    content = f.read()
    # File handle never closed - resource leak
    return content


def calculate_discount(price, discount_percent):
    # No validation - discount could be > 100 or negative
    final_price = price - (price * discount_percent / 100)
    return final_price


def find_user_by_email(email):
    conn = connect_db()
    cursor = conn.cursor()
    # SQL Injection + returning conn without closing
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
    users = cursor.fetchall()
    return users


class UserManager:
    def __init__(self):
        self.users = {}
        self.password = "admin123"  # Hardcoded password

    def add_user(self, user_id, name):
        self.users[user_id] = name

    def get_user(self, user_id):
        return self.users[user_id]  # KeyError if user_id doesn't exist

    def remove_user(self, user_id):
        del self.users[user_id]  # KeyError if user_id doesn't exist

    def get_all_emails(self):
        emails = []
        for id in self.users:  # 'id' shadows built-in
            emails.append(self.users[id])
        return emails

    def export_users(self):
        import json
        data = json.dumps(self.users)
        f = open("users_export.json", "w")
        f.write(data)
        # File never closed

    def unsafe_eval(self, user_input):
        # Dangerous: arbitrary code execution
        result = eval(user_input)
        return result

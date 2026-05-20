import json
import os
import sqlite3


DB_PASSWORD = "super_secret_password_123"


def get_db():
    conn = sqlite3.connect("orders.db")
    return conn


def create_order(user_id, items, total):
    conn = get_db()
    cursor = conn.cursor()
    # SQL injection vulnerability
    query = f"INSERT INTO orders (user_id, items, total) VALUES ('{user_id}', '{json.dumps(items)}', {total})"
    cursor.execute(query)
    conn.commit()
    # Connection never closed


def get_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    # SQL injection
    cursor.execute(f"SELECT * FROM orders WHERE id = {order_id}")
    return cursor.fetchone()


def cancel_order(order_id):
    order = get_order(order_id)
    if order["status"] == "shipped":  # TypeError: tuple indices must be integers
        return {"error": "Cannot cancel shipped order"}
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE orders SET status = 'cancelled' WHERE id = {order_id}")
    conn.commit()


def calculate_total(items):
    total = 0
    for item in items:
        total += item["price"] * item["quantity"]  # No validation, could be negative
    # No rounding - floating point issues
    return total


def apply_coupon(total, coupon_code):
    # Hardcoded coupons with no expiry check
    coupons = {"SAVE20": 20, "SAVE50": 50, "FREE": 100}
    discount = coupons[coupon_code]  # KeyError on invalid coupon
    new_total = total - (total * discount / 100)
    if new_total < 0:
        new_total = 0
    return new_total


def send_email_notification(email, message):
    # Logging sensitive info
    print(f"Sending email to {email}: {message}")
    # No actual email sending, no error handling
    pass


def process_refund(order_id, amount):
    order = get_order(order_id)
    if amount > order[3]:  # Magic number, no named index
        return False
    # No check if refund already processed - double refund possible
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE orders SET refunded = {amount} WHERE id = {order_id}")
    conn.commit()
    return True


def export_orders(start_date, end_date):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM orders WHERE date BETWEEN '{start_date}' AND '{end_date}'")
    orders = cursor.fetchall()
    f = open("orders_export.csv", "w")
    for order in orders:
        f.write(",".join(str(x) for x in order) + "\n")
    # File not closed


def delete_user_data(user_id):
    conn = get_db()
    cursor = conn.cursor()
    # Dangerous: no confirmation, no soft delete, no audit trail
    cursor.execute(f"DELETE FROM orders WHERE user_id = '{user_id}'")
    cursor.execute(f"DELETE FROM users WHERE id = '{user_id}'")
    conn.commit()


class OrderManager:
    def __init__(self):
        self.orders = []
        self.secret_key = "sk_live_order_key_abc123"  # Hardcoded secret

    def add_order(self, order):
        self.orders.append(order)

    def find_order(self, order_id):
        for order in self.orders:
            if order["id"] == order_id:
                return order
        # Returns None implicitly - caller might not handle it

    def get_total_revenue(self):
        return sum(o["total"] for o in self.orders)  # KeyError if "total" missing

    def remove_order(self, order_id):
        order = self.find_order(order_id)
        self.orders.remove(order)  # ValueError if None (order not found)

    def to_json(self):
        return eval(str(self.orders))  # Dangerous eval, should use json.dumps

import json
import os
import pickle
import sqlite3
import subprocess


DB_CONN_STRING = "host=prod-db.transbnk.com user=admin password=Tr@nsbnk2026!"


def get_db():
    return sqlite3.connect("inventory.db")


def add_product(name, price, quantity, category):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO products (name, price, quantity, category) "
        f"VALUES ('{name}', {price}, {quantity}, '{category}')"
    )
    conn.commit()


def search_products(keyword):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{keyword}%'")
    return cursor.fetchall()


def update_stock(product_id, quantity_change):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT quantity FROM products WHERE id = {product_id}")
    current = cursor.fetchone()
    new_quantity = current[0] + quantity_change  # No None check, no negative stock check
    cursor.execute(f"UPDATE products SET quantity = {new_quantity} WHERE id = {product_id}")
    conn.commit()


def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM products WHERE id = {product_id}")
    conn.commit()
    # No check if product exists, no soft delete


def get_low_stock_items(threshold=5):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM products WHERE quantity < {threshold}")
    items = cursor.fetchall()
    for item in items:
        print(f"LOW STOCK ALERT: {item}")  # Should use proper logging
    return items


def import_products(file_path):
    # Dangerous: loading untrusted pickle data
    with open(file_path, "rb") as f:
        products = pickle.load(f)
    for p in products:
        add_product(p["name"], p["price"], p["quantity"], p["category"])


def export_inventory(format_type):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    if format_type == "json":
        f = open("inventory.json", "w")
        json.dump(products, f)
        # File not closed
    elif format_type == "csv":
        f = open("inventory.csv", "w")
        for p in products:
            f.write(",".join(str(x) for x in p) + "\n")
        # File not closed


def run_report(report_name):
    # Command injection vulnerability
    result = subprocess.run(f"python reports/{report_name}.py", shell=True, capture_output=True)
    return result.stdout.decode()


def calculate_inventory_value():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT price, quantity FROM products")
    products = cursor.fetchall()
    total = 0
    for price, qty in products:
        total += price * qty  # No handling for None values
    return total


def apply_bulk_discount(category, discount_percent):
    conn = get_db()
    cursor = conn.cursor()
    # No validation on discount_percent
    cursor.execute(
        f"UPDATE products SET price = price * (1 - {discount_percent}/100) WHERE category = '{category}'"
    )
    conn.commit()


class InventoryManager:
    def __init__(self):
        self.cache = {}
        self.api_token = "tok_live_inventory_abc789xyz"  # Hardcoded token

    def get_product(self, product_id):
        if product_id in self.cache:
            return self.cache[product_id]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")
        product = cursor.fetchone()
        self.cache[product_id] = product
        return product  # Returns None if not found, caller may not handle

    def clear_cache(self):
        self.cache = {}

    def bulk_update(self, updates):
        for id, data in updates.items():
            conn = get_db()  # New connection per iteration - inefficient
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE products SET price = {data['price']}, quantity = {data['quantity']} WHERE id = {id}"
            )
            conn.commit()

    def process_user_query(self, query):
        # Arbitrary code execution
        return eval(query)

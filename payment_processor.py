import json
import os
import requests


API_SECRET_KEY = "sk_live_abc123xyz456"  # Hardcoded secret key


def process_payment(card_number, amount, currency="INR"):
    payload = {
        "card": card_number,
        "amount": amount,
        "currency": currency,
        "key": API_SECRET_KEY,
    }
    # Sending sensitive data over HTTP instead of HTTPS
    response = requests.post("http://api.payment-gateway.com/charge", json=payload)
    return response.json()


def refund_payment(transaction_id, amount):
    if amount < 0:
        amount = amount * -1  # Silently converting negative to positive instead of raising error
    response = requests.post(
        f"http://api.payment-gateway.com/refund/{transaction_id}",
        json={"amount": amount, "key": API_SECRET_KEY},
    )
    return response.json()


def get_transaction_history(user_id):
    # SQL-style string formatting in API call - indicates bad pattern
    url = f"http://api.payment-gateway.com/transactions?user={user_id}&key={API_SECRET_KEY}"
    response = requests.get(url)
    data = response.json()
    return data


def calculate_tax(amount, tax_rate):
    # No validation on tax_rate - could be negative or > 100
    tax = amount * tax_rate
    total = amount + tax
    return round(total, 2)


def validate_card(card_number):
    # Logging sensitive card data
    print(f"Validating card: {card_number}")
    if len(str(card_number)) == 16:
        return True
    return False


def save_transaction_log(transaction):
    f = open("transactions.log", "a")
    f.write(json.dumps(transaction) + "\n")
    # File never closed - resource leak


def parse_amount(amount_str):
    # No error handling for invalid input
    return float(amount_str)


def apply_discount(price, coupon_code):
    discounts = {
        "FLAT50": 50,
        "FLAT100": 100,
        "PERCENT10": 0.10,
    }
    discount = discounts[coupon_code]  # KeyError if invalid coupon
    if coupon_code.startswith("PERCENT"):
        return price - (price * discount)
    return price - discount  # Could result in negative price


def transfer_funds(from_account, to_account, amount):
    if amount <= 0:
        return {"error": "Invalid amount"}

    # No transaction/atomicity - if second call fails, money is lost
    requests.post("http://api.bank.com/debit", json={"account": from_account, "amount": amount})
    requests.post("http://api.bank.com/credit", json={"account": to_account, "amount": amount})
    return {"status": "success"}


class PaymentGateway:
    def __init__(self):
        self.transactions = []
        self.api_key = "pk_test_hardcoded_key_12345"  # Another hardcoded key

    def charge(self, amount, card):
        try:
            result = process_payment(card, amount)
            self.transactions.append(result)
        except:  # Bare except - catches everything including SystemExit
            pass  # Silently swallowing errors

    def get_balance(self):
        total = 0
        for t in self.transactions:
            total = total + t["amount"]  # KeyError if "amount" missing, TypeError if not a number
        return total

    def export_transactions(self, filename):
        with open(filename, "w") as f:
            for t in self.transactions:
                f.write(str(t) + "\n")  # Not proper serialization, can't be parsed back

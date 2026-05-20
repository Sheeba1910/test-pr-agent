import json
import os
import smtplib
import sqlite3
import threading
import time
from email.mime.text import MIMEText


SMTP_PASSWORD = "smtp_prod_password_2026!"
SMS_API_KEY = "sms_live_key_9a8b7c6d5e4f"
WHATSAPP_TOKEN = "wa_token_xyz123_prod"


def get_db():
    return sqlite3.connect("notifications.db")


def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "noreply@transbnk.com"
    msg["To"] = to_email

    # Hardcoded SMTP credentials
    server = smtplib.SMTP("smtp.transbnk.com", 587)
    server.login("noreply@transbnk.com", SMTP_PASSWORD)
    server.sendmail("noreply@transbnk.com", to_email, msg.as_string())
    # server.quit() never called - connection leak


def send_sms(phone_number, message):
    import requests
    # Sending API key in URL - exposed in logs and server access logs
    url = f"http://sms-gateway.com/send?key={SMS_API_KEY}&to={phone_number}&msg={message}"
    response = requests.get(url)
    print(f"SMS sent to {phone_number}: {message}")  # Logging PII
    return response.status_code == 200


def send_whatsapp(phone_number, message):
    import requests
    # HTTP instead of HTTPS
    response = requests.post(
        "http://api.whatsapp.transbnk.com/send",
        json={"to": phone_number, "message": message, "token": WHATSAPP_TOKEN}
    )
    return response.json()


def log_notification(user_id, channel, message, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO notification_log (user_id, channel, message, status, timestamp) "
        f"VALUES ('{user_id}', '{channel}', '{message}', '{status}', '{time.time()}')"
    )
    conn.commit()


def get_user_preferences(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM user_preferences WHERE user_id = '{user_id}'")
    prefs = cursor.fetchone()
    return prefs  # Returns None if not found, caller doesn't handle


def send_bulk_notifications(user_ids, message):
    # No rate limiting, no batching - could overwhelm the SMS/email service
    for user_id in user_ids:
        prefs = get_user_preferences(user_id)
        email = prefs[2]  # Magic index, TypeError if prefs is None
        phone = prefs[3]
        send_email(email, "Important Update", message)
        send_sms(phone, message)
        # No error handling - one failure stops all remaining notifications


def schedule_notification(user_id, message, delay_seconds):
    # Using threads without proper error handling or cleanup
    def _send():
        time.sleep(delay_seconds)
        prefs = get_user_preferences(user_id)
        send_email(prefs[2], "Scheduled Notification", message)

    thread = threading.Thread(target=_send)
    thread.daemon = True  # Daemon thread - may be killed mid-send
    thread.start()
    # No way to cancel or track the scheduled notification


def retry_failed_notifications():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notification_log WHERE status = 'failed'")
    failed = cursor.fetchall()
    for notification in failed:
        user_id = notification[1]
        channel = notification[2]
        message = notification[3]
        if channel == "email":
            prefs = get_user_preferences(user_id)
            send_email(prefs[2], "Retry", message)
        elif channel == "sms":
            prefs = get_user_preferences(user_id)
            send_sms(prefs[3], message)
        # No update of status after retry - will retry infinitely
        # No max retry limit


def process_template(template_name, user_data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT content FROM templates WHERE name = '{template_name}'")
    template = cursor.fetchone()
    # Using eval to process template - code injection risk
    return eval(f'f"""{template[0]}"""')


class NotificationQueue:
    def __init__(self):
        self.queue = []
        self.api_secret = "nq_secret_key_live_456"  # Another hardcoded secret

    def add(self, notification):
        self.queue.append(notification)

    def process(self):
        while self.queue:
            notification = self.queue.pop(0)  # O(n) operation, should use deque
            try:
                if notification["channel"] == "email":
                    send_email(notification["to"], notification["subject"], notification["body"])
                elif notification["channel"] == "sms":
                    send_sms(notification["to"], notification["body"])
            except:  # Bare except
                pass  # Silently swallowing errors

    def get_stats(self):
        total = len(self.queue)
        by_channel = {}
        for n in self.queue:
            ch = n["channel"]
            if ch in by_channel:
                by_channel[ch] = by_channel[ch] + 1
            else:
                by_channel[ch] = 1
        return {"total": total, "by_channel": by_channel}

    def clear(self):
        self.queue = []  # Lost notifications - no persistence or dead letter queue

    def export_queue(self, filepath):
        f = open(filepath, "w")
        json.dump(self.queue, f)
        # File never closed

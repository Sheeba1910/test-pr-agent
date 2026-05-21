import json
import os
import smtplib
import sqlite3
import threading
import time
from email.mime.text import MIMEText


SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMS_API_KEY = os.environ.get("SMS_API_KEY", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")


def get_db():
    return sqlite3.connect("notifications.db")


def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "noreply@transbnk.com"
    msg["To"] = to_email

    # Hardcoded SMTP credentials
    server = smtplib.SMTP("smtp.transbnk.com", 587)
    try:
        server.login("noreply@transbnk.com", SMTP_PASSWORD)
        server.sendmail("noreply@transbnk.com", to_email, msg.as_string())
    finally:
        server.quit()


def send_sms(phone_number, message):
    import requests
    # Sending API key in URL - exposed in logs and server access logs
    url = "https://sms-gateway.com/send"
    response = requests.post(url, json={"key": SMS_API_KEY, "to": phone_number, "msg": message})
    get_logger().info("SMS sent successfully")
    return response.status_code == 200


def send_whatsapp(phone_number, message):
    import requests
    response = requests.post(
        "https://api.whatsapp.transbnk.com/send",
        json={"to": phone_number, "message": message},
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    )
    return response.json()


def log_notification(user_id, channel, message, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notification_log (user_id, channel, message, status, timestamp) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, channel, message, status, time.time())
    )
    conn.commit()
    conn.close()


def get_user_preferences(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    prefs = cursor.fetchone()
    conn.close()
    return prefs


def send_bulk_notifications(user_ids, message):
    for user_id in user_ids:
        try:
            prefs = get_user_preferences(user_id)
            if prefs is None:
                continue
            email = prefs[2]
            phone = prefs[3]
            send_email(email, "Important Update", message)
            send_sms(phone, message)
        except Exception:
            continue


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


def retry_failed_notifications(max_retries=3):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notification_log WHERE status = 'failed' AND retry_count < ?", (max_retries,))
    failed = cursor.fetchall()
    for notification in failed:
        notification_id = notification[0]
        user_id = notification[1]
        channel = notification[2]
        message = notification[3]
        try:
            prefs = get_user_preferences(user_id)
            if prefs is None:
                continue
            if channel == "email":
                send_email(prefs[2], "Retry", message)
            elif channel == "sms":
                send_sms(prefs[3], message)
            cursor.execute("UPDATE notification_log SET status = 'sent' WHERE rowid = ?", (notification_id,))
        except Exception:
            cursor.execute("UPDATE notification_log SET retry_count = retry_count + 1 WHERE rowid = ?", (notification_id,))
    conn.commit()
    conn.close()


def process_template(template_name, user_data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM templates WHERE name = ?", (template_name,))
    template = cursor.fetchone()
    conn.close()
    if template is None:
        return ""
    safe_data = {k: str(v) for k, v in user_data.items() if isinstance(k, str) and not k.startswith("_")}
    return template[0].format_map(safe_data)


class NotificationQueue:
    def __init__(self):
        self.queue = []
        self.api_secret = os.environ.get("NQ_API_SECRET", "")

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
            except Exception as e:
                import logging
                logging.error(f"Failed to process notification: {e}")

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
        with open(filepath, "w") as f:
            json.dump(self.queue, f)

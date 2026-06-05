# =============================================================
#  Intruder Detection and Alert — Python Alert Server
#  Runtime : Python 3
#  Libs    : Flask, requests
#
#  Two responsibilities:
#  1. Listen for HTTP GET /alert from ESP32 on local network
#  2. On alert received → send Telegram message to user
#
#  Also serves live camera feed page at /feed
#  IP Webcam app on smartphone streams MJPEG at port 8080
#
#  Why Flask over a raw socket server?
#  Flask gives clean route handling, runs on 0.0.0.0 (accepts
#  connections from any device on LAN, not just localhost), and
#  separates the alert endpoint from the feed endpoint cleanly.
#
#  Why Telegram over email?
#  Sub-second push notification delivery vs 5-8s SMTP latency.
#  Telegram Bot API is a simple HTTPS POST — no auth complexity,
#  no app passwords, no SMTP rate limits.
# =============================================================

from flask import Flask
from datetime import datetime
import requests

app = Flask(__name__)

# ─── Telegram Bot configuration ──────────────────────────────
# Create a bot via @BotFather on Telegram → get token
# Get your chat_id by messaging @userinfobot
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID"

# ─── IP Webcam feed (smartphone running IP Webcam app) ───────
# Replace with your phone's local IP address
CAMERA_IP   = "192.168.1.X"
CAMERA_PORT = 8080
FEED_URL    = f"http://{CAMERA_IP}:{CAMERA_PORT}/video"

# ─── Send Telegram alert ─────────────────────────────────────
def send_telegram_alert(timestamp, feed_link):
    """
    Send intrusion alert via Telegram Bot API.
    Message includes timestamp and clickable link to live feed.
    Telegram delivers push notifications in under 1 second.
    """
    message = (
        f"🚨 INTRUDER ALERT\n"
        f"Door breach detected at {timestamp}\n"
        f"Live feed: {feed_link}"
    )

    url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id"    : TELEGRAM_CHAT_ID,
        "text"       : message,
        "parse_mode" : "HTML"
    }

    try:
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            print(f"[Telegram] Alert sent at {timestamp}")
        else:
            print(f"[Telegram] Failed — HTTP {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[Telegram] Request error: {e}")

# ─── Route: /alert — called by ESP32 on breach ───────────────
@app.route('/alert', methods=['GET'])
def handle_alert():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feed_link = f"http://192.168.1.X:5000/feed"

    print(f"[ESP32] Breach received at {timestamp}")
    send_telegram_alert(timestamp, feed_link)

    return f"Alert processed at {timestamp}", 200

# ─── Route: /feed — serves live camera feed page ─────────────
@app.route('/feed', methods=['GET'])
def serve_feed():
    """
    Serves an HTML page embedding the IP Webcam MJPEG stream.
    MJPEG is natively supported by all modern browsers via <img>.
    No plugin or video player required.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Live Feed</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ margin: 0; background: #000; display: flex;
           flex-direction: column; align-items: center;
           justify-content: center; min-height: 100vh; }}
    h2  {{ color: #ff4444; font-family: monospace;
           letter-spacing: 3px; margin-bottom: 1rem; }}
    img {{ width: 100%; max-width: 800px; border: 2px solid #ff4444; }}
  </style>
</head>
<body>
  <h2>⚠ LIVE FEED — BREACH DETECTED</h2>
  <img src="{FEED_URL}" alt="Live camera feed"/>
</body>
</html>"""
    return html, 200

# ─── Entry point ─────────────────────────────────────────────
if __name__ == '__main__':
    print("Alert server started. Listening for ESP32 on port 5000...")
    print(f"Feed page: http://0.0.0.0:5000/feed")
    # 0.0.0.0 accepts connections from all devices on local network
    # not just localhost — required for mobile access via email link
    app.run(host='0.0.0.0', port=5000, debug=False)

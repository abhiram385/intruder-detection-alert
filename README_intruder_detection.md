# Intruder Detection and Alert System

Real-time door breach detection using ESP32 and MC-38 magnetic reed switch, with instant Telegram push notification and live IP camera feed. Detects door opening within 600ms, delivers alert in under 2 seconds — no cloud infrastructure, no subscription fees.

---

## Overview

A magnetic reed switch mounted on the door frame monitors circuit continuity. When the door opens, the ESP32 detects the state change, confirms the breach via a debounce routine, and sends an HTTP request to a local Python Flask server. The server dispatches a Telegram push notification containing the timestamp and a direct link to the live camera feed served over the local network.

Tested across 20 trials — 0 false positives, 0 missed detections.

---

## Hardware

| Component | Details |
|-----------|---------|
| Microcontroller | ESP32 DevKit V1 (CP2102, 30-pin) |
| Door sensor | MC-38 magnetic reed switch |
| Resistor | 4.7kΩ pull-up (3.3V → GPIO13) |
| Camera | Smartphone running IP Webcam app |
| Interface | GPIO13 — sensor signal wire |
| Power | USB 5V via CP2102 |

---

## Circuit

```
3.3V ──[4.7kΩ]──┬── GPIO13 (ESP32)
                 │
              MC-38 reed switch
                 │
               GND
```

**Logic state table:**

| Door State | GPIO Voltage | ESP32 Reading | Action |
|------------|-------------|---------------|--------|
| Closed (magnet near) | LOW (GND) | Logic 0 | Monitor |
| Open (magnet removed) | HIGH (3.3V) | Logic 1 | Trigger alert |

The 4.7kΩ pull-up holds GPIO13 firmly at 3.3V when the sensor opens. Without it, the undriven pin floats and picks up ambient noise, causing false triggers.

---

## System Architecture

```
MC-38 Door Sensor
    │
    │  GPIO13 · 4.7kΩ pull-up · 200ms poll
    ▼
ESP32 DevKit
    ├─ Read GPIO13 every 200ms
    ├─ Debounce: 3 consecutive HIGH = confirmed breach (600ms)
    ├─ Set breach flag (resets on door close — 1 alert per event)
    └─ HTTP GET → http://[laptop-ip]:5000/alert
         │
         │  Wi-Fi · LAN · HTTP
         ▼
Python Flask Server (laptop)
    ├─ /alert → send Telegram push notification
    │    └─ Message: timestamp + live feed link
    └─ /feed  → serve HTML page with MJPEG stream
         │
         │  Telegram Bot API · HTTPS
         ▼
Recipient's Phone
    └─ Telegram push notification → tap link → live feed
         │
         │  LAN · MJPEG stream
         ▼
IP Webcam App (smartphone)
    └─ Live camera feed at http://[phone-ip]:8080/video
```

---

## Alert Pipeline Timing

| Stage | Time |
|-------|------|
| Door open → breach confirmed (debounce) | ~600ms |
| ESP32 → Flask HTTP request | ~700–900ms |
| Flask → Telegram API dispatch | ~500ms |
| Telegram push notification delivery | < 1s |
| **Total: door open → phone notification** | **~2–3 seconds** |

---

## Results (20 trials)

| Metric | Result |
|--------|--------|
| False positives | 0 |
| Missed detections | 0 |
| Successful alerts | 20/20 |
| Average end-to-end latency | ~2.5s |

---

## Setup

### Hardware
1. Mount MC-38 switch body on door frame, magnet on door — align within 15mm when closed
2. Connect MC-38 wire 1 → GPIO13, wire 2 → GND
3. Connect 4.7kΩ resistor between 3.3V and GPIO13

### ESP32 Firmware
1. Open `intruder_detection_esp32.ino` in Arduino IDE
2. Set credentials:
   ```c
   const char* ssid      = "YOUR_WIFI";
   const char* pass      = "YOUR_PASS";
   const char* alert_url = "http://[LAPTOP-IP]:5000/alert";
   ```
3. Flash to ESP32 (board: ESP32 Dev Module)

### Python Server
1. Install dependencies:
   ```bash
   pip install flask requests
   ```
2. Create a Telegram bot via @BotFather → copy token
3. Get your chat ID via @userinfobot
4. Set in `alert_server.py`:
   ```python
   TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
   TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID"
   CAMERA_IP          = "YOUR_PHONE_IP"
   ```
5. Run:
   ```bash
   python alert_server.py
   ```

### IP Webcam
1. Install IP Webcam on Android
2. Start server → note the IP and port (default 8080)
3. Keep app in foreground, screen-on, phone plugged in

---

## Dependencies

**ESP32:**
- WiFi, HTTPClient — ESP32 Arduino core

**Python:**
- Flask (`pip install flask`)
- requests (`pip install requests`)

---

## Cost Comparison

| Item | Cost |
|------|------|
| ESP32 DevKit | ~₹350 |
| MC-38 sensor | ~₹80 |
| 4.7kΩ resistor | ~₹2 |
| **Total BOM** | **~₹432** |
| Commercial equivalent | ₹6000+ |

---

## Files

| File | Description |
|------|-------------|
| `intruder_detection_esp32.ino` | ESP32 firmware — sensor monitoring + HTTP trigger |
| `alert_server.py` | Python Flask server — Telegram alert + camera feed |

---

## Author

**Abhiram Kurella** (K.S.S Abhiram — 23071A1095)  
B.Tech Electronics and Instrumentation Engineering  
VNR Vignana Jyothi Institute of Engineering & Technology (2023–2027)  
abhiram.kurella@gmail.com

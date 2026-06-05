/* =============================================================
 *  Intruder Detection and Alert — ESP32 Firmware
 *  Hardware : ESP32 DevKit V1 (CP2102, 30-pin)
 *  Sensor   : MC-38 Magnetic Reed Switch (GPIO13, 4.7kΩ pull-up)
 *  Output   : HTTP GET to Python alert server on local network
 *
 *  Working principle:
 *  MC-38 reed switch mounted on door frame, magnet on door.
 *  Door closed → magnet near switch → contacts closed → GPIO LOW.
 *  Door open   → magnet removed    → contacts open  → GPIO HIGH.
 *  4.7kΩ pull-up holds GPIO13 firmly at 3.3V when sensor open,
 *  eliminating float and noise on an undriven pin.
 *
 *  Debounce:
 *  3 consecutive HIGH readings (200ms apart = 600ms window)
 *  required before breach is confirmed. Eliminates false triggers
 *  from mechanical contact bounce at moment of door opening.
 *  One alert per breach event — flag resets only when door closes.
 * ============================================================= */

#include <WiFi.h>
#include <HTTPClient.h>

/* ─── Wi-Fi credentials ─────────────────────────────────────── */
const char* ssid = "YOUR_WIFI";
const char* pass = "YOUR_PASS";

/* ─── Python alert server (laptop local IP, port 5000) ──────── */
const char* alert_url = "http://192.168.1.X:5000/alert";

/* ─── Sensor configuration ──────────────────────────────────── */
#define SENSOR_PIN        13    /* GPIO13 — MC-38 signal wire    */
#define DEBOUNCE_READS    3     /* Consecutive HIGH reads needed */
#define POLL_INTERVAL_MS  200   /* Read every 200ms              */

/* ─── State ─────────────────────────────────────────────────── */
int     consecutive_high = 0;
bool    breach_active    = false;

/* ─── Send HTTP GET to Python alert server ───────────────────── */
void triggerAlert() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Not connected — alert not sent");
        return;
    }

    HTTPClient http;
    http.begin(alert_url);
    int response = http.GET();

    if (response > 0) {
        Serial.printf("[Alert] Sent — server responded HTTP %d\n", response);
    } else {
        Serial.printf("[Alert] Failed — error %d\n", response);
    }
    http.end();
}

void setup() {
    Serial.begin(115200);

    /* GPIO13 as input — external 4.7kΩ pull-up handles bias */
    pinMode(SENSOR_PIN, INPUT);

    /* Connect to Wi-Fi */
    WiFi.begin(ssid, pass);
    Serial.print("Connecting to Wi-Fi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected. IP: " + WiFi.localIP().toString());
    Serial.println("Monitoring started. Waiting for breach...");
}

void loop() {
    int reading = digitalRead(SENSOR_PIN);

    if (reading == HIGH) {
        /* Door open — magnet removed — pin pulled HIGH by resistor */
        consecutive_high++;

        if (consecutive_high >= DEBOUNCE_READS && !breach_active) {
            /* Confirmed breach — 3 consecutive HIGH readings */
            breach_active = true;
            Serial.println("[BREACH] Door opened — triggering alert");
            triggerAlert();
        }
    } else {
        /* Door closed — magnet present — pin pulled LOW by sensor */
        consecutive_high = 0;

        if (breach_active) {
            breach_active = false;
            Serial.println("[SECURE] Door closed — system rearmed");
        }
    }

    delay(POLL_INTERVAL_MS);
}

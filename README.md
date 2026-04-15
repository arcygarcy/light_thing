# 🕯️ Candle Controller

A lightweight, parallel Tuya light controller using Python, MQTT, and a sleek web dashboard. This setup bypasses the official Tuya app for fast, local control while remaining accessible from anywhere via the web.

---

## 🛠️ Components

1.  **Dashboard (`index.html`)**: A dark-mode web UI that publishes commands to an MQTT broker via WebSockets.
2.  **Listener (`listener.py`)**: A Python script running on a local device (like a Raspberry Pi) that listens for MQTT commands and toggles bulbs in parallel via `tinytuya`.

---

## 📦 Setup

### 1. Requirements
*   Python 3.7+
*   `tinytuya`
*   `paho-mqtt`

### 2. Configuration (Local Only)
Create a `config.json` file on your device (this file is ignored by Git to keep your keys safe):
```json
{
    "MQTT_TOPIC": "your/secret/topic/here",
    "LIGHTS": {
        "candle_1": {
            "id": "DEVICE_ID", 
            "key": "LOCAL_KEY",
            "ip": "192.168.4.x",
            "version": 3.5
        }
    }
}
```
*Use `config.example.json` as a blueprint.*

### 3. Run the Listener
On your Raspberry Pi or local server:
```bash
python3 -m venv venv
source venv/bin/activate
pip install tinytuya paho-mqtt
python3 listener.py
```

### 4. Deploy the Dashboard
*   Update the `TOPIC` in the `<script>` tag of `index.html` to match your `config.json`.
*   Host `index.html` on **GitHub Pages**, **Netlify**, or your own domain.

---

## 🔒 Security Note
*   **Tuya Keys**: These are stored **locally** in `config.json` and never leave your local network.
*   **MQTT Topic**: Use a long, random string for your `MQTT_TOPIC` to prevent unauthorized access, as the public broker (`broker.hivemq.com`) is visible to others.

---

## 🚀 Features
*   **Parallel Toggling**: Uses Python threading to turn all bulbs on/off simultaneously.
*   **Zero Port Forwarding**: Uses outbound MQTT connections to bypass router firewalls.
*   **Modern UI**: Glassmorphism design with mobile-first responsiveness.

# 🕯️ Light Thing

A lightweight, parallel Tuya light controller using Python, MQTT, and a sleek web dashboard. This setup bypasses the official Tuya app for fast, local control while remaining accessible from anywhere via the web.

---

## 🛠️ Project Structure

- **`index.html`**: The frontend dashboard (Hosted on GitHub Pages).
- **`/listener`**: The backend Python service that talks to your bulbs locally.

---

## 📦 Setup

### 1. Requirements
*   Python 3.7+
*   `tinytuya`
*   `paho-mqtt`

### 2. Configuration (Local Only)
Create a `config.json` file inside the `listener/` directory (this file is ignored by Git to keep your keys safe). Use `listener/config.example.json` as a blueprint.

### 3. Run the Listener
On your Raspberry Pi or local server:
```bash
python3 -m venv venv
source venv/bin/activate
pip install tinytuya paho-mqtt
python3 listener/listener.py
```

### 4. Deploy the Dashboard
*   Update the `TOPIC_CMD` and `TOPIC_STATUS` in the `<script>` tag of `index.html` to match your `config.json`.
*   Ensure the `CNAME` file contains your custom domain.
*   Push to GitHub and enable GitHub Pages in the repository settings.

---

## 🚀 Features

-   **Parallel Toggling**: Uses Python threading to turn all bulbs on/off simultaneously.
-   **Modern UI**: Glassmorphism design with an 8-bit style bulb icon.
-   **Color Grid**: 7 vibrant presets + 1 custom "Mood Ring" picker.
-   **Apply Settings**: Queue up your brightness and color, then hit "Apply" to update the whole room.
-   **Real-time Sync**: Large central status ring glows when the lights are confirmed to be ON.
-   **Zero Port Forwarding**: Uses outbound MQTT connections to bypass router firewalls.

---

## 🔒 Security
*   **Tuya Keys**: Stored locally in `listener/config.json`. Never commit this file.
*   **MQTT Topic**: Use a long, random string for your MQTT topics to ensure only your dashboard can control your lights.

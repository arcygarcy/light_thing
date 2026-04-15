import tinytuya
import paho.mqtt.client as mqtt
import json
import threading
import os
import time

# --- LOAD CONFIG FROM FILE ---
CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
    print(f"Error: {CONFIG_FILE} not found. Please create it first.")
    exit(1)

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

CANDLE_LIGHTS = config["LIGHTS"]
MQTT_TOPIC = config["MQTT_TOPIC"]
STATUS_TOPIC = config.get("STATUS_TOPIC", "adam/lights/candle_controller/status")

# --- MQTT CONFIG ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_light_status(name, light_data):
    try:
        d = tinytuya.BulbDevice(
            dev_id=light_data['id'], 
            address=light_data['ip'], 
            local_key=light_data['key'], 
            version=light_data['version']
        )
        d.set_socketTimeout(3)
        status = d.status()
        if status and 'dps' in status:
            dps = status['dps']
            # DP 20: Power, 21: Mode, 22: Brightness, 24: Color
            is_on = dps.get('20', False)
            brightness = dps.get('22', 0)
            color_mode = dps.get('21', 'white')
            
            return {
                "name": name,
                "state": "on" if is_on else "off",
                "brightness": int(brightness / 10) if brightness else 0,
                "mode": color_mode
            }
    except Exception as e:
        print(f"  [STATUS] FAILED: {name} error: {e}")
    return None

def publish_all_status(client):
    print("  [STATUS] Polling all lights...")
    for name, data in CANDLE_LIGHTS.items():
        status = get_light_status(name, data)
        if status:
            client.publish(STATUS_TOPIC, json.dumps(status))
            print(f"  [STATUS] Published status for {name}")

def status_polling_loop(client):
    while True:
        publish_all_status(client)
        time.sleep(60) # Poll every minute

def toggle_light(name, light_data, action, value=None):
    try:
        d = tinytuya.BulbDevice(
            dev_id=light_data['id'], 
            address=light_data['ip'], 
            local_key=light_data['key'], 
            version=light_data['version']
        )
        d.set_socketTimeout(3)
        
        status = None
        if action == "on":
            status = d.turn_on()
        elif action == "off":
            status = d.turn_off()
        elif action == "brightness":
            val = int(value) * 10
            status = d.set_brightness(val)
        elif action == "color":
            r, g, b = hex_to_rgb(value)
            status = d.set_colour(r, g, b)
        
        if status and 'Error' not in str(status):
            print(f"  [PARALLEL] SUCCESS: {name} -> {action} {value if value else ''}")
        else:
            print(f"  [PARALLEL] FAILED: {name} returned error: {status}")
    except Exception as light_err:
        print(f"  [PARALLEL] FAILED: {name} error: {light_err}")

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to: {MQTT_TOPIC}")
    # Initial status sync
    threading.Thread(target=publish_all_status, args=(client,)).start()

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"\n--- Command Received: {payload} ---")
        
        action = payload.get("action")
        target = payload.get("target", "all")
        value = payload.get("value")

        if action == "status":
            threading.Thread(target=publish_all_status, args=(client,)).start()
            return
        
        lights_to_toggle = []
        if target == "all":
            lights_to_toggle = list(CANDLE_LIGHTS.items())
        elif target in CANDLE_LIGHTS:
            lights_to_toggle = [(target, CANDLE_LIGHTS[target])]
            
        for name, light_data in lights_to_toggle:
            t = threading.Thread(target=toggle_light, args=(name, light_data, action, value))
            t.start()
            
    except Exception as e:
        print(f"Error processing message: {e}")

# Setup MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("Starting Light Listener (Full Control Mode)...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start background status polling
poll_thread = threading.Thread(target=status_polling_loop, args=(client,), daemon=True)
poll_thread.start()

client.loop_forever()

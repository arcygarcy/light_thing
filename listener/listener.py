import tinytuya
import paho.mqtt.client as mqtt
import json
import threading
import os
import time

# --- LOAD CONFIG FROM FILE (Robust Path) ---
# This ensures it finds config.json even if run from the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

if not os.path.exists(CONFIG_FILE):
    print(f"Error: {CONFIG_FILE} not found. Please create it first.")
    exit(1)

print("Loading configuration...")
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

CANDLE_LIGHTS_CONFIG = config["LIGHTS"]
MQTT_TOPIC = config["MQTT_TOPIC"]
STATUS_TOPIC = config.get("STATUS_TOPIC", "adam/lights/candle_controller/status")

# --- MQTT CONFIG ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

# --- PERSISTENT DEVICE OBJECTS ---
devices = {}
for name, cfg in CANDLE_LIGHTS_CONFIG.items():
    d = tinytuya.BulbDevice(dev_id=cfg['id'], address=cfg['ip'], local_key=cfg['key'], version=cfg['version'])
    d.set_socketTimeout(3)
    d.set_socketRetryLimit(1)
    devices[name] = d

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def toggle_light(name, action, value=None):
    try:
        d = devices[name]
        if action == "on": d.turn_on()
        elif action == "off": d.turn_off()
        elif action == "brightness":
            d.set_brightness(int(value) * 10)
        elif action == "color":
            r, g, b = hex_to_rgb(value)
            d.set_mode('colour') 
            d.set_colour(r, g, b)
        elif action == "white":
            d.set_mode('white')
            d.set_brightness(1000)
        elif action == "reset":
            d.turn_on()
            time.sleep(0.1)
            d.set_mode('white')
            time.sleep(0.1)
            d.set_brightness(1000)
            d.set_colourtemp(300) 
        print(f"  [CMD] {name} -> {action}")
    except Exception as e:
        print(f"  [CMD] Error on {name}: {e}")

def get_light_status(name):
    try:
        d = devices[name]
        status = d.status()
        if status and 'dps' in status:
            dps = status['dps']
            return {
                "name": name,
                "state": "on" if dps.get('20', False) else "off",
                "brightness": int(dps.get('22', 0) / 10),
                "mode": dps.get('21', 'white')
            }
    except: pass
    return None

def publish_all_status(client):
    results = []
    for name in devices:
        status = get_light_status(name)
        if status: results.append(status)
    
    if results:
        is_on = any(r['state'] == 'on' for r in results)
        summary = {
            "room_state": "on" if is_on else "off",
            "devices": results
        }
        client.publish(STATUS_TOPIC, json.dumps(summary))

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        threading.Thread(target=publish_all_status, args=(client,), daemon=True).start()

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")
        target = payload.get("target", "all")
        value = payload.get("value")

        if action == "status":
            threading.Thread(target=publish_all_status, args=(client,), daemon=True).start()
            return
        
        targets = list(devices.keys()) if target == "all" else [target]
        for name in targets:
            threading.Thread(target=toggle_light, args=(name, action, value), daemon=True).start()
        
        time.sleep(1)
        threading.Thread(target=publish_all_status, args=(client,), daemon=True).start()
            
    except Exception as e:
        print(f"Error: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def poll_loop():
    while True:
        time.sleep(30) 
        publish_all_status(client)

threading.Thread(target=poll_loop, daemon=True).start()
print("Starting Listener (Room Mode)...")
client.loop_forever()

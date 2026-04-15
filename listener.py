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

def get_light_status(name):
    try:
        d = devices[name]
        status = d.status()
        if status and 'dps' in status:
            dps = status['dps']
            is_on = dps.get('20', False)
            brightness = dps.get('22', 0)
            mode = dps.get('21', 'white')
            return {
                "name": name,
                "state": "on" if is_on else "off",
                "brightness": int(brightness / 10) if brightness else 0,
                "mode": mode
            }
    except Exception:
        pass
    return None

def publish_all_status(client):
    for name in devices:
        status = get_light_status(name)
        if status:
            client.publish(STATUS_TOPIC, json.dumps(status))
        time.sleep(0.5)

def status_polling_loop(client):
    while True:
        time.sleep(60)
        publish_all_status(client)

def toggle_light(name, action, value=None):
    try:
        d = devices[name]
        if action == "on": d.turn_on()
        elif action == "off": d.turn_off()
        elif action == "brightness":
            d.set_brightness(int(value) * 10)
        elif action == "color":
            r, g, b = hex_to_rgb(value)
            d.set_mode('colour') # Force color mode
            d.set_colour(r, g, b)
        elif action == "reset":
            d.turn_on()
            d.set_mode('white')
            d.set_brightness(1000)
            d.set_colourtemp(0) # 0 is warm white
        print(f"  [CMD] {name} -> {action}")
    except Exception as e:
        print(f"  [CMD] Error on {name}: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe(MQTT_TOPIC)
    threading.Thread(target=publish_all_status, args=(client,)).start()

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")
        target = payload.get("target", "all")
        value = payload.get("value")

        if action == "status":
            threading.Thread(target=publish_all_status, args=(client,)).start()
            return
        
        targets = list(devices.keys()) if target == "all" else [target]
        for name in targets:
            threading.Thread(target=toggle_light, args=(name, action, value)).start()
            
    except Exception as e:
        print(f"Error: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
threading.Thread(target=status_polling_loop, args=(client,), daemon=True).start()
client.loop_forever()

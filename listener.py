import tinytuya
import paho.mqtt.client as mqtt
import json
import threading
import os

# --- LOAD CONFIG FROM FILE ---
CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
    print(f"Error: {CONFIG_FILE} not found. Please create it first.")
    exit(1)

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

CANDLE_LIGHTS = config["LIGHTS"]
MQTT_TOPIC = config["MQTT_TOPIC"]

# --- MQTT CONFIG ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

def toggle_light(name, light_data, action):
    try:
        d = tinytuya.BulbDevice(
            dev_id=light_data['id'], 
            address=light_data['ip'], 
            local_key=light_data['key'], 
            version=light_data['version']
        )
        d.set_socketTimeout(3)
        
        if action == "on":
            status = d.turn_on()
        else:
            status = d.turn_off()
        
        if status and 'Error' not in str(status):
            print(f"  [PARALLEL] SUCCESS: {name} is {action.upper()}")
        else:
            print(f"  [PARALLEL] FAILED: {name} returned error: {status}")
    except Exception as light_err:
        print(f"  [PARALLEL] FAILED: {name} error: {light_err}")

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"\n--- Parallel Command Received: {payload} ---")
        
        target = payload.get("target")
        action = payload.get("action")
        
        lights_to_toggle = []
        if target == "all":
            lights_to_toggle = list(CANDLE_LIGHTS.items())
        elif target in CANDLE_LIGHTS:
            lights_to_toggle = [(target, CANDLE_LIGHTS[target])]
            
        threads = []
        for name, light_data in lights_to_toggle:
            t = threading.Thread(target=toggle_light, args=(name, light_data, action))
            t.start()
            threads.append(t)
            
    except Exception as e:
        print(f"Error processing message: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("Starting Light Listener (Config File Mode)...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()

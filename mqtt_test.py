import paho.mqtt.client as mqtt
import ssl
import time
import json

# MQTT Configuration
BROKER_URL = "mqtts://mqtt.dhan.co"
CONFIG_MQTT_CLIENT_ID = "mqtt-12x"
CONFIG_MQTT_USERNAME = "device"
CONFIG_MQTT_PASSWORD = "device"
STOCKDOCK_CONFIG_TOPIC = "stockdock/screen/bse-indices"

# Callback when connected
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        print("Successfully connected to MQTT broker")
        client.subscribe(STOCKDOCK_CONFIG_TOPIC)
        print(f"Subscribed to {STOCKDOCK_CONFIG_TOPIC}")
    else:
        print(f"Failed to connect with code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}")
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        print(f"Data type: {type(data)}")
        print(f"Data sample: {data[:2] if isinstance(data, list) else data}")
    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Raw payload: {msg.payload}")

# Callback when disconnected
def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")

# Create MQTT client
client = mqtt.Client(client_id=CONFIG_MQTT_CLIENT_ID, clean_session=True)
client.username_pw_set(CONFIG_MQTT_USERNAME, CONFIG_MQTT_PASSWORD)

# Set callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Set up TLS
client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
client.tls_insecure_set(False)

# Connect to broker
host = BROKER_URL.replace("mqtts://", "")
port = 8443

print(f"Connecting to {host}:{port}...")
client.connect(host, port, 60)

# Start the loop
client.loop_start()

# Keep the script running for a while to receive messages
try:
    print("Waiting for messages... (Press Ctrl+C to exit)")
    for i in range(30):
        time.sleep(1)
        print(f"Waiting... {i+1}/30 seconds")
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    client.loop_stop()
    client.disconnect()
    print("Disconnected from broker") 
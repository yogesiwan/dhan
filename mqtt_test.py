import paho.mqtt.client as mqtt
import ssl
import json
import time

# MQTT Configuration
BROKER_URL = "mqtts://mqtt.dhan.co"
CONFIG_MQTT_CLIENT_ID = "mqtt-12x"
CONFIG_MQTT_USERNAME = "device"
CONFIG_MQTT_PASSWORD = "device"
STOCKDOCK_CONFIG_TOPIC = "stockdock/screen/nse-indices"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        print("Successfully connected to MQTT broker")
        client.subscribe(STOCKDOCK_CONFIG_TOPIC)
        print(f"Subscribed to topic: {STOCKDOCK_CONFIG_TOPIC}")
    else:
        print(f"Failed to connect. Error code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        print("\n=== Received MQTT Message ===")
        print(f"Topic: {msg.topic}")
        print(f"Number of items: {len(data) if isinstance(data, list) else 'Not a list'}")
        
        if isinstance(data, list):
            for item in data:
                if all(key in item for key in ['key', 'ltp', 'p_ch']):
                    print(f"\nIndex ID: {item['key']}")
                    print(f"Last Trade Price: {item['ltp']}")
                    print(f"Percentage Change: {item['p_ch']}%")
                    print(f"Other fields: {', '.join(k for k in item.keys() if k not in ['key', 'ltp', 'p_ch'])}")
                else:
                    print(f"\nIncomplete data received: {item}")
    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Raw message: {msg.payload}")

def main():
    client = mqtt.Client(client_id=CONFIG_MQTT_CLIENT_ID, clean_session=True)
    client.username_pw_set(CONFIG_MQTT_USERNAME, CONFIG_MQTT_PASSWORD)
    
    # Set up TLS
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    client.tls_insecure_set(False)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Extract host and port
    host = BROKER_URL.replace("mqtts://", "")
    port = 8443
    
    try:
        print(f"Connecting to {host}:{port}")
        client.connect(host, port, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting from MQTT broker...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
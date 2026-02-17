import paho.mqtt.client as mqtt
import json
from datetime import datetime

def on_connect(client, userdata, flags, rc):
    print(f"Connected! Code: {rc}")
    client.subscribe("chili/detections")
    print("Subscribed to: chili/detections")
    print("-" * 60)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"[{data['datetime']}] {data['class']} - Confidence: {data['confidence']:.2f}")
    except Exception as e:
        print(f"Raw message: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker.hivemq.com...")
client.connect("broker.hivemq.com", 1883, 60)
client.loop_forever()
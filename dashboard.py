from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from collections import Counter
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chili-detection-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store recent detections (last 100)
recent_detections = []
detection_stats = Counter()

def on_connect(client, userdata, flags, rc):
    print(f"MQTT Connected! Code: {rc}")
    client.subscribe("chili/detections")
    print("Subscribed to: chili/detections")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        
        # Add to recent detections
        recent_detections.insert(0, data)
        if len(recent_detections) > 100:
            recent_detections.pop()
        
        # Update statistics
        detection_stats[data['class']] += 1
        
        # Emit to all connected clients
        socketio.emit('new_detection', data, namespace='/dashboard')
        
        print(f"[{data['datetime']}] {data['class']} - Confidence: {data['confidence']:.2f}")
    except Exception as e:
        print(f"Error processing message: {e}")

# Setup MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    print("Connecting to broker.hivemq.com...")
    mqtt_client.connect("broker.hivemq.com", 1883, 60)
    mqtt_client.loop_forever()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/detections')
def get_detections():
    return jsonify({
        'recent': recent_detections[:50],
        'stats': dict(detection_stats)
    })

@socketio.on('connect', namespace='/dashboard')
def handle_connect():
    print('Client connected')
    emit('initial_data', {
        'recent': recent_detections[:50],
        'stats': dict(detection_stats)
    })

if __name__ == '__main__':
    # Start MQTT in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    
    print("Starting dashboard server on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

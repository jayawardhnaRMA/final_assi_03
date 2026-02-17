"""
Raspberry Pi Inference Script
Real-time chili disease detection from camera feed
Optimized for Raspberry Pi 4 (4GB)
"""

from ultralytics import YOLO
import cv2
import time
import argparse
import json
import sys
import os

# Add GPS module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gps'))

try:
    from gps_parser import GPSReader
    GPS_AVAILABLE = True
except ImportError:
    print("WARNING: GPS module not available. Location tracking disabled.")
    GPS_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("WARNING: RPi.GPIO not available. LED control disabled.")
    GPIO_AVAILABLE = False

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    print("WARNING: paho-mqtt not available. Remote monitoring disabled.")
    print("Install with: pip install paho-mqtt")
    MQTT_AVAILABLE = False

# LED GPIO pin mappings
LED_PINS = {
    'antraknosa': 17,      # Red LED
    'cabai_normal': 27,    # Green LED
    'lalat_buah': 22       # Blue LED
}

def setup_leds():
    """Initialize GPIO pins for LED control"""
    if not GPIO_AVAILABLE:
        return False
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup all LED pins as outputs
        for pin in LED_PINS.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)  # Turn off initially
        
        print("LEDs initialized successfully")
        print(f"  Red (antraknosa): GPIO {LED_PINS['antraknosa']}")
        print(f"  Green (cabai_normal): GPIO {LED_PINS['cabai_normal']}")
        print(f"  Blue (lalat_buah): GPIO {LED_PINS['lalat_buah']}")
        return True
    except Exception as e:
        print(f"Failed to setup LEDs: {e}")
        return False

def control_leds(detected_classes):
    """Control LEDs based on detected diseases"""
    if not GPIO_AVAILABLE:
        return
    
    try:
        # Turn off all LEDs first
        for pin in LED_PINS.values():
            GPIO.output(pin, GPIO.LOW)
        
        # Turn on LEDs for detected classes
        for class_name in detected_classes:
            if class_name in LED_PINS:
                GPIO.output(LED_PINS[class_name], GPIO.HIGH)
    except Exception as e:
        print(f"LED control error: {e}")

def cleanup_leds():
    """Cleanup GPIO pins"""
    if GPIO_AVAILABLE:
        try:
            GPIO.cleanup()
        except:
            pass

def setup_mqtt(broker="broker.hivemq.com", port=1883, client_id=None):
    """Setup MQTT client for remote monitoring"""
    if not MQTT_AVAILABLE:
        return None
    
    try:
        if not client_id:
            client_id = f"chili_monitor_{int(time.time())}"
        
        # Handle both old and new paho-mqtt versions
        try:
            # Try new API (paho-mqtt >= 2.0)
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
        except (AttributeError, TypeError):
            # Fall back to old API (paho-mqtt < 2.0)
            client = mqtt.Client(client_id)
        
        client.connect(broker, port, 60)
        client.loop_start()
        print(f"MQTT connected to {broker}:{port}")
        print(f"Client ID: {client_id}")
        return client
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        return None

def publish_detection(mqtt_client, topic, detection_data):
    """Publish detection to MQTT broker"""
    if mqtt_client and MQTT_AVAILABLE:
        try:
            payload = json.dumps(detection_data)
            mqtt_client.publish(topic, payload, qos=1)
        except Exception as e:
            print(f"MQTT publish error: {e}")

def setup_camera(width=416, height=416, fps=30):
    """Initialize camera with specified settings"""
    # Try different camera indices (0 for USB, sometimes 1 for Pi Camera)
    for camera_id in [0, 1]:
        cap = cv2.VideoCapture(camera_id)
        if cap.isOpened():
            print(f"Camera {camera_id} opened successfully")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, fps)
            return cap
    
    print("ERROR: Could not open camera")
    return None

def run_inference(model_path, show_display=True, save_video=False, frame_skip=1,
                  enable_mqtt=False, mqtt_broker="broker.hivemq.com", mqtt_topic="chili/detections",
                  enable_gps=False):
    """Run real-time inference on camera feed"""
    
    print("=" * 60)
    print("Chili Disease Detection - Raspberry Pi")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Frame skip: {frame_skip} (process every {frame_skip} frame(s))")
    print(f"MQTT: {'Enabled' if enable_mqtt else 'Disabled'}")
    print(f"GPS: {'Enabled' if enable_gps else 'Disabled'}")
    print(f"Press 'q' to quit")
    print("=" * 60)
    
    # Clear previous session file to start fresh
    session_file = "current_session.json"
    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"\nCleared previous session data")
    
    # Load the TFLite model
    print("\nLoading model...")
    model = YOLO(model_path, task='detect')
    
    # Setup GPS
    gps_reader = None
    if enable_gps and GPS_AVAILABLE:
        print("\nSetting up GPS...")
        gps_reader = GPSReader()
        if gps_reader.connect():
            print("GPS connected successfully")
            # Start reading GPS data in background
            import threading
            gps_thread_running = True
            
            def gps_background_reader():
                while gps_thread_running:
                    gps_reader.read_gps_data()
                    time.sleep(0.1)
            
            gps_thread = threading.Thread(target=gps_background_reader, daemon=True)
            gps_thread.start()
        else:
            print("Failed to connect to GPS")
            gps_reader = None
    elif enable_gps and not GPS_AVAILABLE:
        print("\nGPS requested but not available")
    
    # Setup MQTT
    mqtt_client = None
    if enable_mqtt:
        print("\nSetting up MQTT...")
        mqtt_client = setup_mqtt(broker=mqtt_broker)
        if mqtt_client:
            print(f"Publishing to topic: {mqtt_topic}")
    
    # Setup LEDs
    print("\nSetting up LEDs...")
    leds_enabled = setup_leds()
    if not leds_enabled:
        print("Running without LED control")
    
    # Setup camera
    print("\nSetting up camera...")
    cap = setup_camera(width=416, height=416)
    if cap is None:
        cleanup_leds()
        return
    
    # Video writer setup (if saving)
    video_writer = None
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter('output.mp4', fourcc, 20.0, (416, 416))
    
    # Performance tracking
    frame_count = 0
    inference_count = 0
    start_time = time.time()
    fps_display = 0
    
    # Detection tracking
    detections_log = []
    
    print("\nStarting inference...\n")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            frame_count += 1
            
            # Skip frames to improve FPS
            if frame_count % frame_skip != 0:
                if show_display:
                    cv2.imshow('Chili Disease Detection', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            inference_count += 1
            
            # Run inference
            inference_start = time.time()
            results = model.predict(
                source=frame,
                imgsz=416,
                conf=0.5,  # Confidence threshold
                iou=0.45,  # NMS threshold
                verbose=False,
                device='cpu'  # Raspberry Pi uses CPU
            )
            inference_time = time.time() - inference_start
            
            # Get annotated frame
            annotated_frame = results[0].plot()
            
            # Calculate FPS
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                fps_display = inference_count / elapsed_time
            
            # Add FPS and inference time to frame
            cv2.putText(annotated_frame, f'FPS: {fps_display:.1f}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f'Inference: {inference_time*1000:.0f}ms', (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Log detections and control LEDs
            detections = results[0].boxes
            detected_classes = set()
            
            # Define valid disease classes to detect
            VALID_CLASSES = ['antraknosa', 'cabai_normal', 'lalat_buah']
            
            if len(detections) > 0:
                for box in detections:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = model.names[cls_id]
                    
                    # Only process detections from our 3 target classes
                    if class_name not in VALID_CLASSES:
                        continue
                    
                    detected_classes.add(class_name)
                    
                    # Only log and save detections every 20 inferences (same as printing)
                    if inference_count % 20 == 0:
                        # Get GPS coordinates if available
                        gps_coords = None
                        if gps_reader:
                            gps_data = gps_reader.get_current_position()
                            if gps_data:
                                gps_coords = {
                                    'latitude': gps_data['latitude'],
                                    'longitude': gps_data['longitude'],
                                    'altitude': gps_data['altitude'],
                                    'satellites': gps_data['satellites']
                                }
                        
                        detection_info = {
                            'timestamp': time.time(),
                            'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'class': class_name,
                            'confidence': float(conf),
                            'location': gps_coords
                        }
                        detections_log.append(detection_info)
                        
                        # Save to current_session.json immediately for real-time dashboard
                        try:
                            with open(session_file, 'w') as f:
                                json.dump(detections_log, f, indent=2)
                        except Exception as e:
                            print(f"Failed to save session file: {e}")
                        
                        # Print detection
                        location_str = ""
                        if gps_coords:
                            location_str = f" @ ({gps_coords['latitude']:.6f}, {gps_coords['longitude']:.6f})"
                        print(f"Detected: {class_name} ({conf:.2f}){location_str}")
                        
                        # Publish to MQTT
                        if mqtt_client:
                            publish_detection(mqtt_client, mqtt_topic, detection_info)
            
            # Update LED states based on current detections
            control_leds(detected_classes)
            
            # Display frame
            if show_display:
                cv2.imshow('Chili Disease Detection', annotated_frame)
            
            # Save video
            if save_video and video_writer:
                video_writer.write(annotated_frame)
            
            # Print stats every 5 seconds
            if inference_count % (5 * fps_display) == 0 and inference_count > 0:
                print(f"Stats - FPS: {fps_display:.2f}, Total detections: {len(detections_log)}")
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        # Cleanup
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("Session Summary")
        print("=" * 60)
        print(f"Total frames: {frame_count}")
        print(f"Inferences run: {inference_count}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average FPS: {fps_display:.2f}")
        print(f"Total detections: {len(detections_log)}")
        
        # Disease distribution
        if detections_log:
            print("\nDetection Summary:")
            disease_counts = {}
            for det in detections_log:
                disease_counts[det['class']] = disease_counts.get(det['class'], 0) + 1
            
            for disease, count in disease_counts.items():
                print(f"  - {disease}: {count}")
        
        # Save detections log to JSON
        if detections_log:
            # Save to current_session.json for real-time dashboard
            session_file = "current_session.json"
            try:
                with open(session_file, 'w') as f:
                    json.dump(detections_log, f, indent=2)
                print(f"\nSession detections: {session_file}")
            except Exception as e:
                print(f"Failed to save session file: {e}")
            
            # Also save timestamped backup
            log_file = f"detections_{int(time.time())}.json"
            try:
                with open(log_file, 'w') as f:
                    json.dump(detections_log, f, indent=2)
                print(f"Backup saved to: {log_file}")
            except Exception as e:
                print(f"Failed to save backup: {e}")
        
        print("=" * 60)
        
        cap.release()
        if video_writer:
            video_writer.release()
        cv2.destroyAllWindows()
        
        if mqtt_client and MQTT_AVAILABLE:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            print("MQTT disconnected")
        
        if gps_reader:
            gps_reader.close()
            print("GPS disconnected")
        
        cleanup_leds()

def main():
    parser = argparse.ArgumentParser(description='Chili Disease Detection on Raspberry Pi')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to TFLite model file')
    parser.add_argument('--no-display', action='store_true',
                       help='Run without display (headless mode)')
    parser.add_argument('--save-video', action='store_true',
                       help='Save output video')
    parser.add_argument('--frame-skip', type=int, default=1,
                       help='Process every Nth frame (1=all frames, 2=every other frame)')
    parser.add_argument('--mqtt', action='store_true',
                       help='Enable MQTT publishing for remote monitoring')
    parser.add_argument('--mqtt-broker', type=str, default='broker.hivemq.com',
                       help='MQTT broker address (default: broker.hivemq.com)')
    parser.add_argument('--mqtt-topic', type=str, default='chili/detections',
                       help='MQTT topic for publishing detections (default: chili/detections)')
    parser.add_argument('--gps', action='store_true',
                       help='Enable GPS location tracking for detections')
    
    args = parser.parse_args()
    
    run_inference(
        model_path=args.model,
        show_display=not args.no_display,
        save_video=args.save_video,
        frame_skip=args.frame_skip,
        enable_mqtt=args.mqtt,
        mqtt_broker=args.mqtt_broker,
        mqtt_topic=args.mqtt_topic,
        enable_gps=args.gps
    )

if __name__ == "__main__":
    main()

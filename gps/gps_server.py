from flask import Flask, render_template, jsonify
import threading
import time
from gps_parser import GPSReader

app = Flask(__name__)

# Global GPS data
gps_data = {
    'latitude': None,
    'longitude': None,
    'altitude': None,
    'satellites': 0,
    'fix_quality': 0,
    'last_update': None
}

gps_reader = None
gps_thread_running = False

def gps_reading_thread():
    """Background thread to continuously read GPS data"""
    global gps_data, gps_reader, gps_thread_running
    
    gps_reader = GPSReader()
    if not gps_reader.connect():
        print("Failed to connect to GPS module")
        return
    
    print("GPS reader started")
    
    while gps_thread_running:
        try:
            data = gps_reader.read_gps_data()
            if data:
                gps_data.update(data)
                gps_data['last_update'] = time.strftime('%Y-%m-%d %H:%M:%S')
            time.sleep(0.1)  # Read frequently
        except Exception as e:
            print(f"Error in GPS thread: {e}")
            time.sleep(1)
    
    gps_reader.close()

@app.route('/')
def index():
    """Main page with map"""
    return render_template('map.html')

@app.route('/api/gps')
def get_gps():
    """API endpoint to get current GPS data"""
    return jsonify(gps_data)

@app.route('/api/status')
def get_status():
    """Check if GPS has a fix"""
    has_fix = gps_data['latitude'] is not None and gps_data['longitude'] is not None
    return jsonify({
        'has_fix': has_fix,
        'satellites': gps_data['satellites'],
        'fix_quality': gps_data['fix_quality'],
        'last_update': gps_data['last_update']
    })

if __name__ == '__main__':
    # Start GPS reading thread
    gps_thread_running = True
    gps_thread = threading.Thread(target=gps_reading_thread, daemon=True)
    gps_thread.start()
    
    # Start Flask server
    print("Starting GPS Map Server on http://0.0.0.0:5000")
    print("Access from browser at http://raspberrypi.local:5000 or http://<pi-ip>:5000")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
        gps_thread_running = False

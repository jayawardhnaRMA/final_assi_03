from flask import Flask, render_template, jsonify, request
import json
import os
import glob
import shutil
from datetime import datetime

app = Flask(__name__)

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_current_session_file():
    """Get the current session detection file"""
    return os.path.join(PROJECT_ROOT, 'current_session.json')

def load_detections(filename=None):
    """Load detections from JSON file"""
    if not filename:
        filename = get_current_session_file()
    
    if not filename or not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r') as f:
            detections = json.load(f)
        
        # Filter detections with valid GPS coordinates
        valid_detections = []
        for det in detections:
            if det.get('location') and det['location'].get('latitude') and det['location'].get('longitude'):
                valid_detections.append(det)
        
        return valid_detections
    except Exception as e:
        print(f"Error loading detections: {e}")
        return []

@app.route('/')
def index():
    """Main dashboard with map and detection list"""
    return render_template('dashboard.html')

@app.route('/api/detections')
def get_detections():
    """API endpoint to get all detections with GPS data"""
    filename = request.args.get('file')
    detections = load_detections(filename)
    
    return jsonify({
        'detections': detections,
        'total': len(detections)
    })

@app.route('/api/detection-files')
def get_detection_files():
    """Get list of available detection files"""
    detection_files = glob.glob(os.path.join(PROJECT_ROOT, 'detections_*.json'))
    
    files_info = []
    for filepath in detection_files:
        filename = os.path.basename(filepath)
        # Extract timestamp from filename
        try:
            timestamp = int(filename.replace('detections_', '').replace('.json', ''))
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except:
            date_str = 'Unknown'
        
        files_info.append({
            'filename': filename,
            'filepath': filepath,
            'date': date_str,
            'size': os.path.getsize(filepath)
        })
    
    # Sort by date descending
    files_info.sort(key=lambda x: x['filename'], reverse=True)
    
    return jsonify({
        'files': files_info,
        'total': len(files_info)
    })

@app.route('/api/stats')
def get_stats():
    """Get detection statistics"""
    detections = load_detections()
    
    if not detections:
        return jsonify({
            'total_detections': 0,
            'disease_counts': {},
            'gps_enabled_count': 0
        })
    
    # Calculate statistics
    disease_counts = {}
    gps_enabled = 0
    
    for det in detections:
        class_name = det.get('class', 'unknown')
        disease_counts[class_name] = disease_counts.get(class_name, 0) + 1
        
        if det.get('location'):
            gps_enabled += 1
    
    return jsonify({
        'total_detections': len(detections),
        'disease_counts': disease_counts,
        'gps_enabled_count': gps_enabled,
        'latest_detection': detections[-1] if detections else None
    })

@app.route('/api/clear-detections', methods=['POST'])
def clear_detections():
    """Archive old detection files and start fresh"""
    try:
        detection_files = glob.glob(os.path.join(PROJECT_ROOT, 'detections_*.json'))
        
        if not detection_files:
            return jsonify({
                'success': True,
                'message': 'No detection files to clear',
                'archived_count': 0
            })
        
        # Create archive directory
        archive_dir = os.path.join(PROJECT_ROOT, f"detections_archive_{int(datetime.now().timestamp())}")
        os.makedirs(archive_dir, exist_ok=True)
        
        # Move files to archive
        archived_count = 0
        for file in detection_files:
            dest = os.path.join(archive_dir, os.path.basename(file))
            shutil.move(file, dest)
            archived_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Archived {archived_count} detection file(s)',
            'archived_count': archived_count,
            'archive_dir': os.path.basename(archive_dir)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/current-location')
def get_current_location():
    """Get current GPS location from the latest detection"""
    detections = load_detections()
    
    if detections and len(detections) > 0:
        # Get the most recent detection with GPS data
        latest = detections[-1]
        location = latest.get('location')
        if location:
            return jsonify(location)
    
    return jsonify({
        'latitude': None,
        'longitude': None,
        'altitude': None,
        'satellites': 0
    })

if __name__ == '__main__':
    print("=" * 60)
    print("Plant Disease Detection Dashboard")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:5000")
    print("Access from browser at:")
    print("  - Local: http://localhost:5000")
    print("  - Network: http://raspberrypi.local:5000")
    print("  - Or: http://<pi-ip>:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

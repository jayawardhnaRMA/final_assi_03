import serial
import pynmea2
import time

class GPSReader:
    def __init__(self, port='/dev/serial0', baudrate=9600):
        """Initialize GPS reader with serial port configuration"""
        self.port = port
        self.baudrate = baudrate
        self.gps = None
        self.current_lat = None
        self.current_lon = None
        self.current_alt = None
        self.satellites = 0
        self.fix_quality = 0
        
    def connect(self):
        """Connect to GPS module"""
        try:
            self.gps = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            return True
        except Exception as e:
            print(f"Error connecting to GPS: {e}")
            return False
    
    def read_gps_data(self):
        """Read and parse GPS data, return latest position"""
        if not self.gps or not self.gps.is_open:
            return None
            
        try:
            if self.gps.in_waiting > 0:
                line = self.gps.readline().decode('utf-8', errors='ignore').strip()
                
                # Parse NMEA sentences
                if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                    try:
                        msg = pynmea2.parse(line)
                        if msg.latitude and msg.longitude:
                            self.current_lat = msg.latitude
                            self.current_lon = msg.longitude
                            self.current_alt = msg.altitude if msg.altitude else 0
                            self.satellites = msg.num_sats if msg.num_sats else 0
                            self.fix_quality = msg.gps_qual if msg.gps_qual else 0
                            
                            return {
                                'latitude': self.current_lat,
                                'longitude': self.current_lon,
                                'altitude': self.current_alt,
                                'satellites': self.satellites,
                                'fix_quality': self.fix_quality,
                                'timestamp': time.time()
                            }
                    except pynmea2.ParseError:
                        pass
        except Exception as e:
            print(f"Error reading GPS: {e}")
            
        return None
    
    def get_current_position(self):
        """Get the last known position"""
        if self.current_lat and self.current_lon:
            return {
                'latitude': self.current_lat,
                'longitude': self.current_lon,
                'altitude': self.current_alt,
                'satellites': self.satellites,
                'fix_quality': self.fix_quality
            }
        return None
    
    def close(self):
        """Close GPS connection"""
        if self.gps and self.gps.is_open:
            self.gps.close()

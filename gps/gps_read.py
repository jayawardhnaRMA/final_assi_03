import serial
import time

# Open serial port (Raspberry Pi UART)
gps = serial.Serial(
    port='/dev/serial0',   # UART on Raspberry Pi
    baudrate=9600,
    timeout=1
)

print("Reading GPS data... Press Ctrl+C to stop.")

try:
    while True:
        if gps.in_waiting > 0:
            line = gps.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(line)

        time.sleep(2)  # wait 2 seconds

except KeyboardInterrupt:
    print("\nStopped by user")

finally:
    gps.close()

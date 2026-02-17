import RPi.GPIO as GPIO
import time

LED_PIN = 17  # GPIO number, not pin number

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)  # LED ON
        time.sleep(1)
        GPIO.output(LED_PIN, GPIO.LOW)   # LED OFF
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

"""
Configuration file for the Pico W irrigation controller.
Edit this file to match your setup.
"""

# WiFi Configuration
WIFI_SSID = "Redacted"
WIFI_PASSWORD = "00000000"

# Server Configuration
SERVER_URL = "http://192.168.68.65:5000"

# Device Configuration
DEVICE_ID = "pico_01"

# Hardware Configuration
MOISTURE_PIN = 30  # AOUT connected to GPIO30
VALVE_PIN = 38    # GPIO pin for MOSFET gate controlling solenoid

# Timing Configuration
CHECK_INTERVAL = 60  # Seconds between readings
RECONNECT_INTERVAL = 10  # Seconds between WiFi reconnection attempts

# Sensor Calibration
# These values need calibration for your specific moisture sensor
MOISTURE_MIN_VALUE = 20000  # ADC value when sensor is in water
MOISTURE_MAX_VALUE = 65000  # ADC value when sensor is in air 
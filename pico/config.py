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
MOISTURE_PIN = 27  # AOUT connected to GPIO27 (ADC1)
VALVE_PIN = 38    # GPIO pin for MOSFET gate controlling solenoid

# Timing Configuration
CHECK_INTERVAL = 60  # Seconds between readings
RECONNECT_INTERVAL = 10  # Seconds between WiFi reconnection attempts

# Sensor Calibration
# Calibrated values for capacitive soil moisture sensor
MOISTURE_MIN_VALUE = 10800  # ADC value when soil is very wet
MOISTURE_MAX_VALUE = 14300  # ADC value when soil is very dry

# Moisture interpretation guide:
# 0-20%:   Very Dry  (around 40593)
# 20-40%:  Dry       (around 36924) - Watering starts
# 40-60%:  Moderate  (around 31421)
# 60-80%:  Moist     (around 25918) - Watering stops
# 80-100%: Very Wet  (around 22249) 
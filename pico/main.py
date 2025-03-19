"""
Irrigation Control System - Pico W Controller
This script runs on a Raspberry Pi Pico W to:
1. Read moisture sensor data
2. Control a solenoid valve
3. Send data to the Raspberry Pi server
4. Check for and execute commands from the server
"""

import network
import urequests
import time
from machine import ADC, Pin
import json
import gc
import machine

# Status LED
led = Pin("LED", Pin.OUT)

def blink_error():
    """Blink LED rapidly to indicate error"""
    for _ in range(5):
        led.toggle()
        time.sleep(0.1)
    led.off()

def blink_success():
    """Blink LED slowly to indicate success"""
    for _ in range(2):
        led.toggle()
        time.sleep(0.5)
    led.off()

# Import configuration
try:
    import config
    print("Loaded configuration from config.py")
    blink_success()  # Indicate config loaded
except ImportError:
    print("Warning: config.py not found, using default configuration")
    blink_error()
    # Default configuration
    class config:
        WIFI_SSID = "Redacted"
        WIFI_PASSWORD = "00000000"
        SERVER_URL = "http://192.168.68.65:5000"
        DEVICE_ID = "pico_01"
        MOISTURE_PIN = 27  # AOUT connected to GPIO27
        VALVE_PIN = 38    # GPIO pin for MOSFET gate controlling solenoid
        CHECK_INTERVAL = 60
        RECONNECT_INTERVAL = 10
        MOISTURE_MIN_VALUE = 10800
        MOISTURE_MAX_VALUE = 14300

# Setup hardware
moisture_sensor = ADC(Pin(config.MOISTURE_PIN))
valve = Pin(config.VALVE_PIN, Pin.OUT)
valve.value(0)  # Ensure valve is OFF at startup

# WiFi connection
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def connect_wifi():
    """Connect to WiFi network"""
    print(f"Connecting to WiFi: {config.WIFI_SSID}")
    
    # Disconnect if already connected
    if wlan.isconnected():
        print("Already connected")
        print(f"IP address: {wlan.ifconfig()[0]}")
        blink_success()
        return True
    
    # Connect to WiFi
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    
    # Wait for connection with timeout
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            print("Connected to WiFi")
            print(f"IP address: {wlan.ifconfig()[0]}")
            blink_success()
            return True
        max_wait -= 1
        print("Waiting for connection...")
        led.toggle()  # Blink while connecting
        time.sleep(1)
    
    print("Failed to connect to WiFi")
    blink_error()
    return False

def update_calibration_values(adc_value):
    """
    Dynamically update calibration values if a reading is outside current range.
    Returns True if values were updated, False otherwise.
    """
    try:
        updated = False
        # If reading is wetter than current min (remember: lower ADC = wetter)
        if adc_value < config.MOISTURE_MIN_VALUE:
            print(f"New minimum ADC value found: {adc_value} (old: {config.MOISTURE_MIN_VALUE})")
            config.MOISTURE_MIN_VALUE = int(round(adc_value))  # Round to nearest integer
            updated = True
            
        # If reading is drier than current max
        elif adc_value > config.MOISTURE_MAX_VALUE:
            print(f"New maximum ADC value found: {adc_value} (old: {config.MOISTURE_MAX_VALUE})")
            config.MOISTURE_MAX_VALUE = int(round(adc_value))  # Round to nearest integer
            updated = True
            
        if updated:
            print("Updating calibration values in config.py...")
            # Update the config file with new values
            with open('config.py', 'r') as f:
                lines = f.readlines()
                
            with open('config.py', 'w') as f:
                for line in lines:
                    if 'MOISTURE_MIN_VALUE' in line and not line.strip().startswith('#'):
                        f.write(f"MOISTURE_MIN_VALUE = {config.MOISTURE_MIN_VALUE}  # ADC value when soil is very wet\n")
                    elif 'MOISTURE_MAX_VALUE' in line and not line.strip().startswith('#'):
                        f.write(f"MOISTURE_MAX_VALUE = {config.MOISTURE_MAX_VALUE}  # ADC value when soil is very dry\n")
                    else:
                        f.write(line)
            print("Calibration values updated successfully")
            return True
    except Exception as e:
        print(f"Error updating calibration: {e}")
        # If there's any error, just continue without updating
        pass
    return False

def read_moisture():
    """Read moisture level from sensor"""
    # Take multiple readings and average them
    readings = []
    for _ in range(10):
        readings.append(moisture_sensor.read_u16())
        time.sleep_ms(100)
    
    # Remove outliers
    mean = sum(readings) / len(readings)
    std_dev = (sum((x - mean) ** 2 for x in readings) / len(readings)) ** 0.5
    filtered = [x for x in readings if abs(x - mean) <= 2 * std_dev]
    
    if not filtered:
        adc_value = int(mean)
    else:
        adc_value = int(sum(filtered) / len(filtered))
    
    # Print both 12-bit ADC value and approximate voltage
    voltage = (adc_value * 3.3) / 4095
    print(f"Raw ADC (12-bit): {adc_value}, Voltage: {voltage:.2f}V")
    
    # Update calibration if reading is outside current range
    if update_calibration_values(adc_value):
        print(f"New calibration - MIN: {config.MOISTURE_MIN_VALUE}, MAX: {config.MOISTURE_MAX_VALUE}")
    
    # Convert to percentage
    moisture_percentage = ((config.MOISTURE_MAX_VALUE - adc_value) / 
                         (config.MOISTURE_MAX_VALUE - config.MOISTURE_MIN_VALUE)) * 100
    
    return max(0, min(100, moisture_percentage)), adc_value

def control_valve(state):
    """Control the solenoid valve (0=OFF, 1=ON)"""
    valve.value(state)
    print(f"Valve turned {'ON' if state else 'OFF'}")

def send_data_to_server(moisture):
    """Send moisture data to server"""
    try:
        moisture_pct, adc_value = moisture
        data = {
            "device_id": config.DEVICE_ID,
            "moisture": moisture_pct,
            "raw_adc_value": adc_value
        }
        
        print("\nSending data to server:")
        print(f"URL: {config.SERVER_URL}/api/sensor-data")
        print(f"Data: {data}")
        
        response = urequests.post(
            f"{config.SERVER_URL}/api/sensor-data",
            headers={'Content-Type': 'application/json'},
            json=data
        )
        
        print(f"Server response code: {response.status_code}")
        print(f"Server response: {response.text}")
        response.close()
        
        if response.status_code == 200:
            print("Data sent successfully!")
            blink_success()  # Indicate successful send
            return True
        else:
            print(f"Server error: {response.status_code}")
            blink_error()  # Indicate failed send
            return False
            
    except Exception as e:
        print(f"Error sending data: {e}")
        print("Network or server might be unreachable")
        blink_error()
        return False

def check_commands():
    """Check for pending commands from server"""
    try:
        response = urequests.get(f"{config.SERVER_URL}/api/commands/{config.DEVICE_ID}")
        data = response.json()
        response.close()
        
        command = data.get('command')
        if command:
            print(f"Received command: {command}")
            
            # Process valve control command
            if command.startswith('valve:'):
                state = int(command.split(':')[1])
                control_valve(state)
                return True
        
        return False
    except Exception as e:
        print(f"Error checking commands: {e}")
        return False

def blink_led(times=1, delay=0.2):
    """Blink the onboard LED"""
    for _ in range(times):
        led.on()
        time.sleep(delay)
        led.off()
        time.sleep(delay)

def main():
    """Main program loop"""
    print(f"Starting irrigation controller - Device ID: {config.DEVICE_ID}")
    print(f"Server URL: {config.SERVER_URL}")
    
    # Initial connection
    if not connect_wifi():
        print("Initial WiFi connection failed. Will retry in main loop.")
        blink_error()
    
    last_reading_time = 0
    
    while True:
        try:
            # Check WiFi connection
            if not wlan.isconnected():
                print("WiFi disconnected. Reconnecting...")
                if not connect_wifi():
                    time.sleep(config.RECONNECT_INTERVAL)
                    continue
            
            # Check if it's time for a new reading
            current_time = time.time()
            if current_time - last_reading_time >= config.CHECK_INTERVAL:
                # Read moisture level
                moisture = read_moisture()
                moisture_pct, adc_value = moisture
                print(f"Moisture: {moisture_pct:.1f}% (ADC: {adc_value})")
                
                # Send data to server
                if send_data_to_server(moisture):
                    last_reading_time = current_time
                
                # Free memory
                gc.collect()
            
            # Check for commands
            check_commands()
            
            # Short sleep to prevent busy waiting
            time.sleep(5)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            blink_error()
            time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        # Ensure valve is OFF when program exits
        valve.value(0)
        print("Valve turned OFF - System shutdown") 
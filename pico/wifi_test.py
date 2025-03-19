"""
WiFi Connection Test Script
Tests WiFi connection and server communication
"""
import network
import urequests
import time
import json
from machine import Pin

# Status LED
led = Pin("LED", Pin.OUT)

# Import configuration
try:
    import config
    print("Loaded configuration from config.py")
except ImportError:
    print("Error: config.py not found!")
    raise

def connect_wifi():
    """Connect to WiFi and return status"""
    print(f"\nConnecting to WiFi: {config.WIFI_SSID}")
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Check if already connected
    if wlan.isconnected():
        print("Already connected")
        print(f"IP address: {wlan.ifconfig()[0]}")
        return True
    
    # Connect to WiFi
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    
    # Wait for connection with timeout
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            print("Connected successfully!")
            print(f"IP address: {wlan.ifconfig()[0]}")
            return True
        max_wait -= 1
        print("Waiting for connection...")
        led.toggle()  # Blink LED while connecting
        time.sleep(1)
    
    print("Failed to connect to WiFi")
    return False

def test_server_connection():
    """Test connection to the server"""
    print(f"\nTesting connection to server: {config.SERVER_URL}")
    
    try:
        # Try to send a test data point
        data = {
            "device_id": config.DEVICE_ID,
            "moisture": 50.0,  # Test value
            "raw_adc_value": 32767  # Test value
        }
        
        print("Sending test data...")
        response = urequests.post(
            f"{config.SERVER_URL}/api/sensor-data",
            headers={'Content-Type': 'application/json'},
            json=data
        )
        
        print(f"Server response status: {response.status_code}")
        response.close()
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return False

def main():
    print("\nPico W Connection Test")
    print("====================")
    
    # Test WiFi
    if not connect_wifi():
        print("\nWiFi connection failed!")
        return
    
    # Test server connection
    if test_server_connection():
        print("\nServer connection successful!")
        # Blink LED rapidly to indicate success
        for _ in range(5):
            led.toggle()
            time.sleep(0.1)
    else:
        print("\nServer connection failed!")
        # Slow blink to indicate failure
        for _ in range(3):
            led.toggle()
            time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"\nError during test: {e}")
    finally:
        led.off() 
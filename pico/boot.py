"""
Boot script for Pico W Irrigation Controller
This script runs automatically on startup and launches the main program.
"""

import machine
import network
import time
import calibrate_gp27

# Setup LED for status indication
led = machine.Pin("LED", machine.Pin.OUT)

print("Starting irrigation controller...")

# Import configuration
try:
    import config
    print("Loaded configuration")
    led.on()
    time.sleep(0.5)
    led.off()
except ImportError:
    print("Failed to load config")
    for _ in range(3):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)

# Setup WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

try:
    print("Connecting to WiFi...")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    
    # Wait for connection with timeout
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            print("Connected to WiFi")
            ip = wlan.ifconfig()[0]
            print("IP address:", ip)
            led.on()
            time.sleep(0.5)
            led.off()
            
            # Start WebREPL
            try:
                import webrepl
                webrepl.start()
                print("WebREPL started")
            except:
                print("WebREPL failed to start")
            break
            
        max_wait -= 1
        print("Waiting for connection...")
        led.toggle()
        time.sleep(1)
    
    if not wlan.isconnected():
        print("WiFi connection failed")
        for _ in range(5):
            led.on()
            time.sleep(0.1)
            led.off()
            time.sleep(0.1)
    
except Exception as e:
    print("WiFi error:", e)
    for _ in range(5):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)

# Start main program
try:
    print("Starting main program...")
    import main
    print("Main program started")
    calibrate_gp27.calibrate()
except Exception as e:
    print("Error starting main program:", e)
    while True:
        led.toggle()
        time.sleep(0.2)




        
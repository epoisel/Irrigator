"""
Boot script for Pico W Irrigation Controller
This script runs automatically on startup and launches the main program.
"""

import time
print("Starting irrigation controller...")
time.sleep(1)  # Give the system a moment to stabilize

try:
    import main
except Exception as e:
    print(f"Error starting main program: {e}")
    # If there's an error, we'll still keep the system running
    # but in a failed state so it's obvious something went wrong
    import machine
    led = machine.Pin("LED", machine.Pin.OUT)
    while True:
        led.toggle()
        time.sleep(0.2)  # Fast blink indicates error 
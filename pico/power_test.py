"""
Power Supply Test Script
Tests the Pico's power supply voltage
"""
from machine import ADC, Pin
import time

# Setup VSYS monitoring
vsys = ADC(Pin(29))  # VSYS monitoring (ADC3)

def read_vsys():
    """Read VSYS voltage (should be ~3.3V)"""
    raw = vsys.read_u16()
    return raw * 3.3 / 65535

def main():
    print("\nPico Power Supply Test")
    print("====================")
    print("VSYS should be around 3.3V")
    print("If it's much lower, there might be a power issue")
    print("\nTime  |  VSYS")
    print("-" * 20)
    
    start_time = time.time()
    try:
        while True:
            vsys = read_vsys()
            elapsed = time.time() - start_time
            print(f"{elapsed:4.1f}s | {vsys:5.2f}V")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    main() 
"""
Voltage Check Script
This script helps verify power supply voltages on various pins
"""
from machine import ADC, Pin
import time

# Setup ADCs for voltage monitoring
vsys = ADC(Pin(29))        # VSYS monitoring (ADC3)
gp27 = ADC(Pin(27))        # Our sensor pin (ADC1)
gp26 = ADC(Pin(26))        # Additional test pin (ADC0)

def read_vsys():
    """Read VSYS voltage (should be ~3.3V)"""
    raw = vsys.read_u16()
    return raw * 3.3 / 65535

def read_gp27():
    """Read GP27 voltage"""
    raw = gp27.read_u16()
    return raw * 3.3 / 65535

def read_gp26():
    """Read GP26 voltage for comparison"""
    raw = gp26.read_u16()
    return raw * 3.3 / 65535

def main():
    print("\nVoltage Check Tool")
    print("=================")
    print("Taking readings every second. Press Ctrl+C to stop.")
    print("\nTime  |  VSYS   |  GP27   |  GP26")
    print("-" * 40)
    
    start_time = time.time()
    try:
        while True:
            vsys = read_vsys()
            sensor = read_gp27()
            test = read_gp26()
            
            elapsed = time.time() - start_time
            print(f"{elapsed:4.1f}s | {vsys:5.2f}V | {sensor:5.2f}V | {test:5.2f}V")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    main() 
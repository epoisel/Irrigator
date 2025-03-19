"""
Simple Calibration Script for Moisture Sensor
"""
from machine import ADC, Pin
import time

# Setup moisture sensor on GP27
moisture_sensor = ADC(Pin(27))

def take_readings():
    """Take multiple readings and return average"""
    readings = []
    print("Taking readings...")
    for i in range(10):
        value = moisture_sensor.read_u16()
        readings.append(value)
        print(f"Reading {i+1}: {value}")
        time.sleep(0.5)
    
    avg = sum(readings) / len(readings)
    return int(avg)

def calibrate():
    print("\n=== Moisture Sensor Calibration ===")
    print("This will help calibrate your sensor.")
    
    # Dry calibration
    print("\nDRY CALIBRATION:")
    print("1. Hold sensor in air")
    print("2. Keep it still")
    input("Press Enter when ready...")
    
    dry_value = take_readings()
    print(f"\nDry reading: {dry_value}")
    
    # Wet calibration
    print("\nWET CALIBRATION:")
    print("1. Put sensor in water up to the marked line")
    print("WARNING: Don't get the electronics wet!")
    input("Press Enter when ready...")
    
    wet_value = take_readings()
    print(f"\nWet reading: {wet_value}")
    
    # Update config.py
    try:
        print("\nUpdating config.py...")
        with open('config.py', 'r') as f:
            lines = f.readlines()
        
        with open('config.py', 'w') as f:
            for line in lines:
                if 'MOISTURE_MIN_VALUE' in line and not line.strip().startswith('#'):
                    f.write(f"MOISTURE_MIN_VALUE = {min(wet_value, dry_value)}  # ADC value when soil is very wet\n")
                elif 'MOISTURE_MAX_VALUE' in line and not line.strip().startswith('#'):
                    f.write(f"MOISTURE_MAX_VALUE = {max(wet_value, dry_value)}  # ADC value when soil is very dry\n")
                else:
                    f.write(line)
        print("Calibration values updated successfully!")
        
    except Exception as e:
        print(f"\nError updating config.py: {e}")
        print("Please manually update these values in config.py:")
        print(f"MOISTURE_MIN_VALUE = {min(wet_value, dry_value)}")
        print(f"MOISTURE_MAX_VALUE = {max(wet_value, dry_value)}")

if __name__ == "__main__":
    try:
        calibrate()
    except KeyboardInterrupt:
        print("\nCalibration cancelled") 
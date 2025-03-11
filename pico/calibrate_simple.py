"""
Simple Calibration Script for Moisture Sensor
This script helps calibrate the moisture sensor by taking readings in dry and wet conditions.
"""

from machine import ADC, Pin
import time

# Setup moisture sensor
MOISTURE_PIN = 30  # AOUT connected to GPIO30
moisture_sensor = ADC(Pin(MOISTURE_PIN))

def take_readings(num_samples=50):
    """Take multiple readings and return the average"""
    readings = []
    print("Taking readings...")
    for i in range(num_samples):
        value = moisture_sensor.read_u16()
        readings.append(value)
        print(f"Reading {i+1}: {value}")
        time.sleep_ms(100)
    
    # Remove outliers (values more than 2 standard deviations from mean)
    mean = sum(readings) / len(readings)
    std_dev = (sum((x - mean) ** 2 for x in readings) / len(readings)) ** 0.5
    filtered = [x for x in readings if abs(x - mean) <= 2 * std_dev]
    
    if not filtered:
        return mean  # If all readings were outliers, return original mean
    
    final_mean = sum(filtered) / len(filtered)
    return int(round(final_mean))

def calibrate():
    """Run the calibration process"""
    print("\n=== Moisture Sensor Calibration ===")
    print("This will help calibrate your moisture sensor.")
    print("We'll take readings in completely dry and wet conditions.")
    
    # Dry calibration
    print("\nDRY CALIBRATION:")
    print("1. Clean and dry the sensor completely")
    print("2. Hold it in the air")
    print("3. Keep it still")
    print("\nPress Enter when ready (or Ctrl+C to cancel)")
    input()
    
    dry_value = take_readings()
    print(f"\nDry reading: {dry_value}")
    
    # Wet calibration
    print("\nWET CALIBRATION:")
    print("1. Get some water in a container")
    print("2. Insert sensor up to the marked line")
    print("3. Keep it still")
    print("WARNING: Don't get the electronics wet!")
    print("\nPress Enter when ready (or Ctrl+C to cancel)")
    input()
    
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
        
        print("\nCalibration values updated successfully!")
        print(f"MIN (wet): {min(wet_value, dry_value)}")
        print(f"MAX (dry): {max(wet_value, dry_value)}")
        
    except Exception as e:
        print(f"\nError updating config.py: {e}")
        print("Please manually update these values in config.py:")
        print(f"MOISTURE_MIN_VALUE = {min(wet_value, dry_value)}")
        print(f"MOISTURE_MAX_VALUE = {max(wet_value, dry_value)}")

if __name__ == '__main__':
    try:
        calibrate()
    except KeyboardInterrupt:
        print("\nCalibration cancelled by user")
    except Exception as e:
        print(f"\nError during calibration: {e}") 
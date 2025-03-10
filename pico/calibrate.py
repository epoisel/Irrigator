"""
Capacitive Soil Moisture Sensor Calibration Script for Pico W
This script helps calibrate the capacitive moisture sensor by taking multiple readings
in different soil conditions to determine the min and max values.
"""

from machine import ADC, Pin
import time

# Setup moisture sensor
MOISTURE_PIN = 30  # AOUT connected to GPIO30
moisture_sensor = ADC(Pin(MOISTURE_PIN))

def take_readings(num_samples=100, delay_ms=50):
    """
    Take multiple readings and return the average and stability metric
    Returns: (average, stability_percentage)
    """
    readings = []
    for _ in range(num_samples):
        readings.append(moisture_sensor.read_u16())
        time.sleep_ms(delay_ms)
    
    # Calculate mean and standard deviation
    mean = sum(readings) / len(readings)
    std_dev = (sum((x - mean) ** 2 for x in readings) / len(readings)) ** 0.5
    
    # Calculate stability as percentage (lower std_dev = more stable)
    stability = max(0, min(100, 100 - (std_dev / mean * 100)))
    
    # Remove extreme outliers (more than 3 standard deviations)
    filtered_readings = [x for x in readings if abs(x - mean) <= 3 * std_dev]
    final_mean = sum(filtered_readings) / len(filtered_readings)
    
    return final_mean, stability

def wait_for_stability(threshold=95, max_attempts=5):
    """
    Wait for sensor readings to stabilize
    Returns: (stable_value, stability_percentage)
    """
    for attempt in range(max_attempts):
        value, stability = take_readings()
        print(f"Stability: {stability:.1f}%")
        if stability >= threshold:
            return value, stability
        print("Waiting for readings to stabilize...")
        time.sleep(1)
    
    # If we couldn't reach threshold, return best effort
    return take_readings()

def calibrate():
    print("\nCapacitive Soil Moisture Sensor Calibration")
    print("=========================================")
    print("\nThis calibration process will help establish the range")
    print("of your capacitive soil moisture sensor using real soil samples.")
    
    # Dry calibration
    print("\n1. DRY SOIL CALIBRATION")
    print("Instructions:")
    print("- Use completely dry soil")
    print("- Insert sensor to the marked line")
    print("- Keep sensor position steady")
    input("Press Enter when ready...")
    
    print("\nTaking dry soil readings...")
    dry_value, dry_stability = wait_for_stability()
    print(f"Dry value: {dry_value:.0f} (Stability: {dry_stability:.1f}%)")
    
    # Wet calibration
    print("\n2. WET SOIL CALIBRATION")
    print("Instructions:")
    print("- Use well-watered but not saturated soil")
    print("- Soil should be as wet as you'd want for your plants")
    print("- Insert sensor to the same depth mark")
    print("- Keep sensor position steady")
    input("Press Enter when ready...")
    
    print("\nTaking wet soil readings...")
    wet_value, wet_stability = wait_for_stability()
    print(f"Wet value: {wet_value:.0f} (Stability: {wet_stability:.1f}%)")
    
    # Validate readings
    if abs(wet_value - dry_value) < 1000:
        print("\nWARNING: The difference between wet and dry readings is very small.")
        print("This might indicate a problem with the sensor or the calibration process.")
        print("Consider repeating the calibration.")
        if not input("\nDo you want to continue anyway? (y/n): ").lower().startswith('y'):
            return
    
    # Calculate and display results
    print("\nCALIBRATION RESULTS")
    print("==================")
    print(f"Dry soil value:  {dry_value:.0f}")
    print(f"Wet soil value:  {wet_value:.0f}")
    print(f"Reading range:   {abs(dry_value - wet_value):.0f}")
    print(f"Dry stability:   {dry_stability:.1f}%")
    print(f"Wet stability:   {wet_stability:.1f}%")
    
    # Update config.py
    try:
        with open('config.py', 'r') as f:
            config_lines = f.readlines()
        
        with open('config.py', 'w') as f:
            for line in config_lines:
                if 'MOISTURE_MIN_VALUE' in line:
                    f.write(f"MOISTURE_MIN_VALUE = {int(min(wet_value, dry_value))}  # ADC value in wet soil\n")
                elif 'MOISTURE_MAX_VALUE' in line:
                    f.write(f"MOISTURE_MAX_VALUE = {int(max(wet_value, dry_value))}  # ADC value in dry soil\n")
                else:
                    f.write(line)
        print("\nConfiguration updated successfully!")
        
        # Provide interpretation guidance
        print("\nINTERPRETATION GUIDE")
        print("===================")
        print("For your soil and sensor:")
        print(f"0-20%:   Very Dry  (around {dry_value:.0f})")
        print(f"20-40%:  Dry       (around {dry_value - (abs(dry_value - wet_value) * 0.2):.0f})")
        print(f"40-60%:  Moderate  (around {dry_value - (abs(dry_value - wet_value) * 0.5):.0f})")
        print(f"60-80%:  Moist     (around {dry_value - (abs(dry_value - wet_value) * 0.8):.0f})")
        print(f"80-100%: Very Wet  (around {wet_value:.0f})")
        
    except Exception as e:
        print(f"\nError updating config.py: {e}")
        print(f"Please manually update these values in config.py:")
        print(f"MOISTURE_MIN_VALUE = {int(min(wet_value, dry_value))}")
        print(f"MOISTURE_MAX_VALUE = {int(max(wet_value, dry_value))}")

if __name__ == '__main__':
    try:
        calibrate()
    except KeyboardInterrupt:
        print("\nCalibration cancelled.")
    except Exception as e:
        print(f"\nError during calibration: {e}") 
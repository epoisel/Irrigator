"""
GP27 Moisture Sensor Calibration Script
This script helps calibrate the moisture sensor connected to GP27 (ADC1).
It takes continuous readings and shows both raw ADC values and calculated voltages.
"""

from machine import ADC, Pin
import time

# Setup ADC on GP27 with full resolution
adc = ADC(Pin(27))  # ADC1 on Pico

def take_readings(duration=5):
    """Take readings for specified duration and return stats"""
    readings = []
    start_time = time.time()
    
    print("\nTaking readings for", duration, "seconds...")
    print("Time  |  ADC Value  | ADC Voltage | Scaled to 5V")
    print("-" * 50)
    
    while time.time() - start_time < duration:
        # Take reading at full 16-bit resolution
        raw = adc.read_u16()
        
        # Calculate voltages (using full 16-bit range)
        adc_voltage = (raw * 3.3) / 65535  # Convert to voltage (0-3.3V)
        scaled_voltage = adc_voltage * (5.0 / 3.3)  # Scale to 5V reference
        
        # Print current reading
        elapsed = time.time() - start_time
        print(f"{elapsed:4.1f}s | {raw:8d} | {adc_voltage:5.2f}V | {scaled_voltage:5.2f}V")
        
        readings.append(raw)
        time.sleep(1)
    
    # Calculate statistics
    avg_value = sum(readings) / len(readings)
    min_value = min(readings)
    max_value = max(readings)
    
    return {
        'average': avg_value,
        'min': min_value,
        'max': max_value,
        'readings': readings
    }

def calibrate():
    print("\nMoisture Sensor Calibration (GP27)")
    print("================================")
    print("\nThis script will help calibrate your moisture sensor.")
    print("We'll take readings in three conditions to establish the range.")
    print("Expected ADC values should be between 10000-65535")
    print("If values are much lower, there might be a wiring issue.")
    
    # Air readings (completely dry)
    input("\nStep 1: Hold sensor in air (completely dry)")
    input("Press Enter when ready...")
    air_stats = take_readings(5)
    
    # Dry soil readings
    input("\nStep 2: Insert sensor in dry soil")
    input("Press Enter when ready...")
    dry_stats = take_readings(5)
    
    # Wet soil/water readings
    input("\nStep 3: Insert sensor in wet soil or water")
    print("WARNING: Only insert up to the marked line!")
    input("Press Enter when ready...")
    wet_stats = take_readings(5)
    
    # Print results
    print("\nCalibration Results")
    print("==================")
    print(f"\nAir Readings:")
    print(f"  Average: {air_stats['average']:.0f}")
    print(f"  Range: {air_stats['min']:.0f} - {air_stats['max']:.0f}")
    
    print(f"\nDry Soil Readings:")
    print(f"  Average: {dry_stats['average']:.0f}")
    print(f"  Range: {dry_stats['min']:.0f} - {dry_stats['max']:.0f}")
    
    print(f"\nWet Readings:")
    print(f"  Average: {wet_stats['average']:.0f}")
    print(f"  Range: {wet_stats['min']:.0f} - {wet_stats['max']:.0f}")
    
    # Validate readings
    if max(air_stats['max'], dry_stats['max'], wet_stats['max']) < 5000:
        print("\nWARNING: Readings are unusually low!")
        print("This might indicate a problem with:")
        print("1. Power supply - Make sure sensor is getting 5V")
        print("2. Wiring - Check all connections")
        print("3. Ground connection - Ensure common ground between sensor and Pico")
        if not input("\nDo you want to continue anyway? (y/n): ").lower().startswith('y'):
            return
    
    # Calculate recommended calibration values
    min_value = min(wet_stats['average'], dry_stats['average'], air_stats['average'])
    max_value = max(wet_stats['average'], dry_stats['average'], air_stats['average'])
    
    print("\nRecommended Calibration Values")
    print("============================")
    print(f"MOISTURE_MIN_VALUE = {int(min_value)}  # Wettest reading")
    print(f"MOISTURE_MAX_VALUE = {int(max_value)}  # Driest reading")
    
    # Offer to update config.py
    if input("\nWould you like to update config.py with these values? (y/n): ").lower() == 'y':
        try:
            with open('config.py', 'r') as f:
                lines = f.readlines()
            
            with open('config.py', 'w') as f:
                for line in lines:
                    if 'MOISTURE_MIN_VALUE' in line and not line.strip().startswith('#'):
                        f.write(f"MOISTURE_MIN_VALUE = {int(min_value)}  # ADC value when soil is very wet\n")
                    elif 'MOISTURE_MAX_VALUE' in line and not line.strip().startswith('#'):
                        f.write(f"MOISTURE_MAX_VALUE = {int(max_value)}  # ADC value when soil is very dry\n")
                    else:
                        f.write(line)
            print("config.py updated successfully!")
        except Exception as e:
            print(f"Error updating config.py: {e}")
            print("Please update the values manually.")

def quick_test():
    """Take continuous readings for testing"""
    print("\nQuick Test Mode")
    print("==============")
    print("Taking continuous readings. Press Ctrl+C to stop.")
    print("Expected ADC values should be between 10000-65535")
    print("\nTime  |  ADC Value  | ADC Voltage | Scaled to 5V")
    print("-" * 50)
    
    start_time = time.time()
    try:
        while True:
            raw = adc.read_u16()
            adc_voltage = (raw * 3.3) / 65535
            scaled_voltage = adc_voltage * (5.0 / 3.3)
            
            elapsed = time.time() - start_time
            print(f"{elapsed:4.1f}s | {raw:8d} | {adc_voltage:5.2f}V | {scaled_voltage:5.2f}V")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    print("\nGP27 Moisture Sensor Calibration Tool")
    print("=================================")
    print("1: Run full calibration")
    print("2: Run quick test (continuous readings)")
    
    choice = input("\nEnter your choice (1 or 2): ")
    
    try:
        if choice == "1":
            calibrate()
        elif choice == "2":
            quick_test()
        else:
            print("Invalid choice. Please run again and select 1 or 2.")
    except KeyboardInterrupt:
        print("\nCalibration cancelled by user")
    except Exception as e:
        print(f"\nError during calibration: {e}") 
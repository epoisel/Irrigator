"""
Moisture Sensor Verification Script
This script helps verify the accuracy and reliability of the moisture sensor readings.
"""

from machine import ADC, Pin
import time

# Setup moisture sensor
MOISTURE_PIN = 30  # AOUT connected to GPIO30
moisture_sensor = ADC(Pin(MOISTURE_PIN))

def test_sensor():
    """Test function to verify sensor readings"""
    print("\n=== Sensor Verification Test ===")
    print("Taking 20 readings with detailed output...")
    
    readings = []
    raw_readings = []
    for i in range(20):
        raw = moisture_sensor.read_u16()
        raw_readings.append(raw)
        readings.append(moisture_sensor.read_u16())
        print(f"Reading {i+1}: Raw ADC: {raw}")
        time.sleep_ms(500)
    
    avg = sum(readings) / len(readings)
    min_val = min(readings)
    max_val = max(readings)
    variation = max_val - min_val
    
    print(f"\nResults:")
    print(f"Average: {avg:.1f}")
    print(f"Min: {min_val}")
    print(f"Max: {max_val}")
    print(f"Variation: {variation} ({(variation/avg)*100:.1f}% of average)")
    
    return raw_readings

def wait_for_user():
    """Wait for user to press Enter"""
    print("Press Enter to continue...")
    while True:
        if input() in ['', '\n', '\r', '\r\n']:
            break
        time.sleep_ms(100)

def verify_sensor_stability():
    """Verify sensor stability in different conditions"""
    print("\n=== Sensor Stability Verification ===")
    print("This test will verify sensor readings in three conditions.")
    print("Follow the prompts and press Enter after each setup.")
    time.sleep(2)  # Give user time to read
    
    print("\nTest 1: Stability in Air")
    print("Hold the sensor in air.")
    wait_for_user()
    air_readings = test_sensor()
    
    print("\nTest 2: Stability in Water")
    print("Place sensor in water up to the marked line.")
    print("WARNING: Don't get the electronics wet!")
    wait_for_user()
    water_readings = test_sensor()
    
    print("\nTest 3: Stability in Damp Soil")
    print("Place sensor in damp (not wet) soil.")
    wait_for_user()
    soil_readings = test_sensor()
    
    # Calculate stability metrics
    air_variation = max(air_readings) - min(air_readings)
    water_variation = max(water_readings) - min(water_readings)
    soil_variation = max(soil_readings) - min(soil_readings)
    
    print("\n=== Final Results ===")
    print(f"Air readings variation: {air_variation}")
    print(f"Water readings variation: {water_variation}")
    print(f"Soil readings variation: {soil_variation}")
    
    # Check if variations are within acceptable range (less than 5% of reading)
    air_avg = sum(air_readings) / len(air_readings)
    water_avg = sum(water_readings) / len(water_readings)
    soil_avg = sum(soil_readings) / len(soil_readings)
    
    print(f"\nAir average: {air_avg:.0f}")
    print(f"Water average: {water_avg:.0f}")
    print(f"Soil average: {soil_avg:.0f}")
    
    print("\nReading Reliability:")
    print(f"Air: {'Good' if air_variation/air_avg < 0.05 else 'Unstable'}")
    print(f"Water: {'Good' if water_variation/water_avg < 0.05 else 'Unstable'}")
    print(f"Soil: {'Good' if soil_variation/soil_avg < 0.05 else 'Unstable'}")

def quick_test():
    """Run a quick test without user interaction"""
    print("\n=== Quick Sensor Test ===")
    print("Taking readings for 10 seconds...")
    print("Keep the sensor still!")
    
    start_time = time.time()
    readings = []
    
    while time.time() - start_time < 10:
        value = moisture_sensor.read_u16()
        readings.append(value)
        print(f"ADC Value: {value}")
        time.sleep_ms(500)
    
    avg = sum(readings) / len(readings)
    min_val = min(readings)
    max_val = max(readings)
    variation = max_val - min_val
    
    print(f"\nTest Results:")
    print(f"Average: {avg:.1f}")
    print(f"Min: {min_val}")
    print(f"Max: {max_val}")
    print(f"Variation: {variation} ({(variation/avg)*100:.1f}% of average)")
    print(f"Stability: {'Good' if variation/avg < 0.05 else 'Unstable'}")

if __name__ == '__main__':
    try:
        verify_sensor_stability()
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
    except Exception as e:
        print(f"\nError during test: {e}") 
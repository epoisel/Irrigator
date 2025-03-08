#!/usr/bin/env python3
"""
Simulation script for generating test data for the irrigation system.
This script simulates a Pico W device sending moisture readings to the backend.
"""

import requests
import time
import random
import argparse
import json
from datetime import datetime

def simulate_device(device_id, server_url, interval=60, duration=3600):
    """
    Simulate a device sending moisture readings to the server.
    
    Args:
        device_id (str): The ID of the simulated device
        server_url (str): The URL of the backend server
        interval (int): Time between readings in seconds
        duration (int): Total simulation time in seconds
    """
    print(f"Starting simulation for device {device_id}")
    print(f"Sending data to {server_url}")
    print(f"Interval: {interval} seconds")
    print(f"Duration: {duration} seconds")
    
    start_time = time.time()
    end_time = start_time + duration
    
    # Initial moisture level (50% - middle of range)
    moisture = 50.0
    
    # Trend direction (1 for increasing, -1 for decreasing)
    trend = -1
    
    while time.time() < end_time:
        # Add some random variation to the moisture level
        moisture += trend * random.uniform(0.5, 2.0)
        
        # Add some noise
        moisture += random.uniform(-1.0, 1.0)
        
        # Keep moisture within realistic bounds (0-100%)
        moisture = max(0.0, min(100.0, moisture))
        
        # Change trend direction if we reach bounds
        if moisture < 10.0:
            trend = 1  # Start increasing
        elif moisture > 90.0:
            trend = -1  # Start decreasing
        
        # Randomly change trend sometimes
        if random.random() < 0.05:
            trend = -trend
        
        # Send data to server
        data = {
            'device_id': device_id,
            'moisture': moisture
        }
        
        try:
            response = requests.post(f"{server_url}/api/sensor-data", json=data)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if response.status_code == 200:
                print(f"[{timestamp}] Sent moisture: {moisture:.1f}% - Success")
                
                # Check for commands
                cmd_response = requests.get(f"{server_url}/api/commands/{device_id}")
                if cmd_response.status_code == 200:
                    cmd_data = cmd_response.json()
                    if cmd_data.get('command'):
                        print(f"[{timestamp}] Received command: {cmd_data['command']}")
                        
                        # If valve command received, simulate effect on moisture
                        if cmd_data['command'].startswith('valve:'):
                            valve_state = int(cmd_data['command'].split(':')[1])
                            if valve_state == 1:
                                print(f"[{timestamp}] Valve turned ON - Moisture will increase")
                                trend = 1  # Start increasing moisture
                            else:
                                print(f"[{timestamp}] Valve turned OFF - Moisture will decrease")
                                trend = -1  # Start decreasing moisture
            else:
                print(f"[{timestamp}] Error sending data: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        # Wait for next interval
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='Simulate an irrigation device')
    parser.add_argument('--device-id', type=str, default='pico_sim_01',
                        help='Device ID for the simulated device')
    parser.add_argument('--server', type=str, default='http://localhost:5000',
                        help='URL of the backend server')
    parser.add_argument('--interval', type=int, default=10,
                        help='Time between readings in seconds')
    parser.add_argument('--duration', type=int, default=3600,
                        help='Total simulation time in seconds (0 for infinite)')
    
    args = parser.parse_args()
    
    # If duration is 0, run indefinitely
    duration = args.duration if args.duration > 0 else float('inf')
    
    try:
        simulate_device(args.device_id, args.server, args.interval, duration)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")

if __name__ == "__main__":
    main() 
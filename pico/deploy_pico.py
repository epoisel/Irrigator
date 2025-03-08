#!/usr/bin/env python3
"""
Deployment script for the Pico W irrigation controller.
This script helps upload the MicroPython code to a connected Pico W.
"""

import os
import sys
import time
import argparse
import serial
import serial.tools.list_ports

def find_pico_port():
    """Find the serial port for the connected Pico W."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        # Look for common Pico descriptors
        if "Pico" in port.description or "USB Serial" in port.description:
            return port.device
    return None

def upload_file(port, filename):
    """Upload a file to the Pico W using REPL."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return False
    
    try:
        # Open serial connection
        ser = serial.Serial(port, 115200, timeout=1)
        
        # Enter REPL mode
        ser.write(b'\r\x03\x03')  # Ctrl+C twice to interrupt any running program
        time.sleep(0.5)
        ser.reset_input_buffer()
        
        # Create the file on Pico
        base_filename = os.path.basename(filename)
        print(f"Uploading {base_filename}...")
        
        # Open file for writing
        ser.write(f"f = open('{base_filename}', 'w')\r\n".encode())
        time.sleep(0.5)
        
        # Write content in chunks
        chunk_size = 256
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            # Escape special characters
            chunk = chunk.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            ser.write(f'f.write("{chunk}")\r\n'.encode())
            time.sleep(0.3)
            # Print progress
            sys.stdout.write(f"\rProgress: {min(i+chunk_size, len(content))}/{len(content)} bytes")
            sys.stdout.flush()
        
        # Close file
        ser.write(b'f.close()\r\n')
        time.sleep(0.5)
        
        print(f"\nFile {base_filename} uploaded successfully!")
        ser.close()
        return True
    
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload MicroPython code to Pico W')
    parser.add_argument('--port', help='Serial port for Pico W (auto-detected if not specified)')
    parser.add_argument('--files', nargs='+', default=['main.py', 'config.py'], 
                        help='Files to upload (default: main.py and config.py)')
    parser.add_argument('--reset', action='store_true', help='Soft reset Pico after upload')
    
    args = parser.parse_args()
    
    # Find Pico port if not specified
    port = args.port
    if not port:
        port = find_pico_port()
        if not port:
            print("Error: Could not find Pico W. Please connect it or specify the port manually.")
            return 1
    
    print(f"Using port: {port}")
    
    # Upload each file
    success = True
    for filename in args.files:
        if not os.path.exists(filename):
            print(f"Error: File {filename} not found.")
            success = False
            continue
        
        if not upload_file(port, filename):
            success = False
    
    # Reset Pico if requested
    if args.reset and success:
        try:
            print("Resetting Pico W...")
            ser = serial.Serial(port, 115200, timeout=1)
            ser.write(b'\r\x04')  # Ctrl+D to soft reset
            ser.close()
            print("Pico W reset successfully!")
        except Exception as e:
            print(f"Error resetting Pico W: {e}")
            success = False
    
    if success:
        print("\nDeployment completed successfully!")
        print("The Pico W should now be running the irrigation controller.")
    else:
        print("\nDeployment completed with errors.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
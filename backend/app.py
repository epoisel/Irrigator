from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import datetime
import time
import threading


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'irrigation.db')

# Watering control constants
WICKING_WAIT_TIME = 60 * 60  # 60 minutes in seconds
WATERING_DURATION = 5 * 60   # 5 minutes in seconds
MAX_DAILY_CYCLES = 4         # Maximum watering cycles per day

# Global state tracking
last_watering_times = {}     # Track last watering time per device
daily_cycles = {}            # Track daily watering cycles per device
last_cycle_reset = {}        # Track when we last reset daily cycles

def init_db():
    """Initialize the database with required tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create moisture_data table with raw_adc_value column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moisture_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        moisture REAL NOT NULL,
        raw_adc_value INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create valve_actions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS valve_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        state INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create automation_rules table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS automation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1,
        low_threshold REAL NOT NULL,
        high_threshold REAL NOT NULL,
        last_watering TEXT,
        daily_cycles INTEGER DEFAULT 0,
        cycles_reset_date TEXT
    )
    ''')

    # Create plant_measurements table with plant_name
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plant_measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        plant_name TEXT NOT NULL DEFAULT 'My Plant',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        height REAL,
        leaf_count INTEGER,
        stem_thickness REAL,
        canopy_width REAL,
        leaf_color INTEGER,
        leaf_firmness INTEGER,
        health_score INTEGER,
        notes TEXT,
        fertilized BOOLEAN DEFAULT 0,
        pruned BOOLEAN DEFAULT 0,
        ph_reading REAL,
        FOREIGN KEY(device_id) REFERENCES automation_rules(device_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Device command queue
device_commands = {}

def can_water_device(device_id, current_time=None):
    """Check if it's safe to water the device based on timing rules."""
    if current_time is None:
        current_time = time.time()
    
    # Initialize tracking for new devices
    if device_id not in last_watering_times:
        last_watering_times[device_id] = 0
    if device_id not in daily_cycles:
        daily_cycles[device_id] = 0
    if device_id not in last_cycle_reset:
        last_cycle_reset[device_id] = current_time
    
    # Reset daily cycles at midnight
    current_date = datetime.datetime.fromtimestamp(current_time).date()
    last_reset_date = datetime.datetime.fromtimestamp(last_cycle_reset[device_id]).date()
    
    if current_date != last_reset_date:
        daily_cycles[device_id] = 0
        last_cycle_reset[device_id] = current_time
    
    # Check timing rules
    time_since_last_water = current_time - last_watering_times[device_id]
    
    return (time_since_last_water >= WICKING_WAIT_TIME and 
            daily_cycles[device_id] < MAX_DAILY_CYCLES)

def update_watering_state(device_id, current_time=None):
    """Update the watering state for a device."""
    if current_time is None:
        current_time = time.time()
    
    last_watering_times[device_id] = current_time
    daily_cycles[device_id] += 1

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Endpoint to receive sensor data from Pico W devices."""
    try:
        data = request.json
        if not data or 'device_id' not in data or 'moisture' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        device_id = data['device_id']
        moisture = float(data['moisture'])
        raw_adc_value = data.get('raw_adc_value')  # New field for ADC value
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO moisture_data (device_id, moisture, raw_adc_value) VALUES (?, ?, ?)',
            (device_id, moisture, raw_adc_value)
        )
        conn.commit()
        conn.close()
        
        # Check automation rules
        check_automation_rules(device_id, moisture)
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/commands/<device_id>', methods=['GET'])
def get_commands(device_id):
    """Endpoint for devices to check for pending commands."""
    if device_id in device_commands:
        command = device_commands.pop(device_id)
        return jsonify({'command': command}), 200
    return jsonify({'command': None}), 200

@app.route('/api/valve/control', methods=['POST'])
def control_valve():
    """Endpoint to manually control a valve."""
    try:
        data = request.json
        if not data or 'device_id' not in data or 'state' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        device_id = data['device_id']
        state = int(data['state'])  # 0 for OFF, 1 for ON
        
        # Store valve action in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO valve_actions (device_id, state) VALUES (?, ?)',
            (device_id, state)
        )
        conn.commit()
        conn.close()
        
        # Queue command for device
        device_commands[device_id] = 'valve:' + str(state)
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/moisture', methods=['GET'])
def get_moisture_analytics():
    """Endpoint to retrieve moisture analytics."""
    try:
        device_id = request.args.get('device_id')
        days = int(request.args.get('days', 1))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        # Calculate timestamp for filtering
        timestamp = datetime.datetime.now() - datetime.timedelta(days=days)
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT * FROM moisture_data 
               WHERE device_id = ? AND timestamp >= ? 
               ORDER BY timestamp''',
            (device_id, timestamp_str)
        )
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/valve', methods=['GET'])
def get_valve_history():
    """Endpoint to retrieve valve action history."""
    try:
        device_id = request.args.get('device_id')
        days = int(request.args.get('days', 1))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        # Calculate timestamp for filtering
        timestamp = datetime.datetime.now() - datetime.timedelta(days=days)
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT * FROM valve_actions 
               WHERE device_id = ? AND timestamp >= ? 
               ORDER BY timestamp DESC''',
            (device_id, timestamp_str)
        )
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation', methods=['GET'])
def get_automation_rules():
    """Endpoint to retrieve automation rules."""
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM automation_rules WHERE device_id = ?',
            (device_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify(dict(row)), 200
        else:
            # Return default values if no rules exist
            return jsonify({
                'device_id': device_id,
                'enabled': 1,
                'low_threshold': 30.0,
                'high_threshold': 70.0
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation', methods=['POST'])
def set_automation_rules():
    """Endpoint to set automation rules."""
    try:
        data = request.json
        if not data or 'device_id' not in data or 'enabled' not in data or \
           'low_threshold' not in data or 'high_threshold' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        device_id = data['device_id']
        enabled = int(data['enabled'])
        low_threshold = float(data['low_threshold'])
        high_threshold = float(data['high_threshold'])
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if rule exists
        cursor.execute(
            'SELECT id FROM automation_rules WHERE device_id = ?',
            (device_id,)
        )
        
        row = cursor.fetchone()
        
        if row:
            # Update existing rule
            cursor.execute(
                '''UPDATE automation_rules 
                   SET enabled = ?, low_threshold = ?, high_threshold = ? 
                   WHERE device_id = ?''',
                (enabled, low_threshold, high_threshold, device_id)
            )
        else:
            # Create new rule
            cursor.execute(
                '''INSERT INTO automation_rules 
                   (device_id, enabled, low_threshold, high_threshold) 
                   VALUES (?, ?, ?, ?)''',
                (device_id, enabled, low_threshold, high_threshold)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_automation_rules(device_id, moisture):
    """Check automation rules and control valve if needed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM automation_rules WHERE device_id = ?',
            (device_id,)
        )
        
        rule = cursor.fetchone()
        conn.close()
        
        if rule and rule['enabled']:
            current_time = time.time()
            
            if moisture <= rule['low_threshold']:
                # Only water if timing rules allow
                if can_water_device(device_id, current_time):
                    # Start watering cycle
                    control_valve_internal(device_id, 1)
                    
                    # Schedule valve turn off after WATERING_DURATION
                    def turn_off_valve():
                        time.sleep(WATERING_DURATION)
                        control_valve_internal(device_id, 0)
                        update_watering_state(device_id)
                    
                    # Start timer thread
                    timer_thread = threading.Thread(target=turn_off_valve)
                    timer_thread.daemon = True
                    timer_thread.start()
            
            elif moisture >= rule['high_threshold']:
                # Turn off valve if moisture is high enough
                control_valve_internal(device_id, 0)
    
    except Exception as e:
        print(f"Error in automation: {str(e)}")

def control_valve_internal(device_id, state):
    """Internal function to control valve and log action."""
    try:
        # Store valve action in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO valve_actions (device_id, state) VALUES (?, ?)',
            (device_id, state)
        )
        conn.commit()
        conn.close()
        
        # Queue command for device
        device_commands[device_id] = 'valve:' + str(state)
    except Exception as e:
        print(f"Error controlling valve: {str(e)}")

def automation_worker():
    """Background worker to periodically check automation rules."""
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all devices with recent moisture data
            cursor.execute('''
                SELECT DISTINCT device_id FROM moisture_data
                WHERE timestamp >= datetime('now', '-1 hour')
            ''')
            
            devices = [row['device_id'] for row in cursor.fetchall()]
            
            for device_id in devices:
                # Get latest moisture reading
                cursor.execute('''
                    SELECT moisture FROM moisture_data
                    WHERE device_id = ?
                    ORDER BY timestamp DESC LIMIT 1
                ''', (device_id,))
                
                row = cursor.fetchone()
                if row:
                    moisture = row['moisture']
                    check_automation_rules(device_id, moisture)
            
            conn.close()
        except Exception as e:
            print(f"Error in automation worker: {str(e)}")
        
        # Check every 5 minutes
        time.sleep(300)

# Start automation worker in a background thread
automation_thread = threading.Thread(target=automation_worker, daemon=True)
automation_thread.start()

@app.route('/api/measurements', methods=['POST'])
def add_measurement():
    """Endpoint to add a new plant measurement."""
    try:
        data = request.json
        if not data or 'device_id' not in data:
            return jsonify({'error': 'Device ID is required'}), 400

        # Extract data with defaults for optional fields
        device_id = data['device_id']
        plant_name = data.get('plant_name', 'My Plant')
        height = data.get('height')
        leaf_count = data.get('leaf_count')
        stem_thickness = data.get('stem_thickness')
        canopy_width = data.get('canopy_width')
        leaf_color = data.get('leaf_color')
        leaf_firmness = data.get('leaf_firmness')
        health_score = data.get('health_score')
        notes = data.get('notes')
        fertilized = data.get('fertilized', False)
        pruned = data.get('pruned', False)
        ph_reading = data.get('ph_reading')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO plant_measurements (
                device_id, plant_name, height, leaf_count, stem_thickness, canopy_width,
                leaf_color, leaf_firmness, health_score, notes,
                fertilized, pruned, ph_reading
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_id, plant_name, height, leaf_count, stem_thickness, canopy_width,
            leaf_color, leaf_firmness, health_score, notes,
            fertilized, pruned, ph_reading
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'id': cursor.lastrowid}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/measurements/<device_id>', methods=['GET'])
def get_measurements(device_id):
    """Endpoint to retrieve plant measurements."""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Calculate timestamp for filtering
        timestamp = datetime.datetime.now() - datetime.timedelta(days=days)
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM plant_measurements 
            WHERE device_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (device_id, timestamp_str))
        
        rows = cursor.fetchall()
        measurements = [dict(row) for row in rows]
        conn.close()
        
        return jsonify(measurements), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 
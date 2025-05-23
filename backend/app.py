from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import sqlite3
import os
import datetime
import time
import threading
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler
import math
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization"],
        "expose_headers": ["Content-Type", "Content-Length"],
        "supports_credentials": False,
        "max_age": 86400
    }
})

# Setup logging
log_file = os.path.join(os.path.dirname(__file__), 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Add OPTIONS handler for preflight requests
@app.after_request
def after_request(response):
    if request.method == 'OPTIONS':
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Max-Age', '86400')
    return response

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'irrigation.db')
app.logger.info(f"Using database at: {os.path.abspath(DB_PATH)}")

# Device command queue
device_commands = {}

# Watering state tracking
last_watering_times = {}
daily_cycles = {}
last_cycle_reset = {}
manual_override = {}  # Track manual valve overrides

# Photo upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Default watering control constants (will be overridden by profiles)
DEFAULT_WICKING_WAIT_TIME = 60 * 60  # 60 minutes in seconds
DEFAULT_WATERING_DURATION = 5 * 60   # 5 minutes in seconds
DEFAULT_MAX_DAILY_CYCLES = 4         # Maximum watering cycles per day
DEFAULT_SENSING_INTERVAL = 5 * 60    # 5 minutes in seconds

# In-memory state tracking 
device_profiles = {}  # Maps device_id to active profile

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
        notes TEXT,
        fertilized BOOLEAN DEFAULT 0,
        pruned BOOLEAN DEFAULT 0,
        FOREIGN KEY(device_id) REFERENCES automation_rules(device_id)
    )
    ''')

    # Create plant_photos table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plant_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        measurement_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(measurement_id) REFERENCES plant_measurements(id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

def get_device_profile(device_id):
    """Get the active watering profile for a device."""
    # Return from cache if available
    if device_id in device_profiles:
        return device_profiles[device_id]
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First try to get the default profile for this device
        cursor.execute(
            'SELECT * FROM watering_profiles WHERE device_id = ? AND is_default = 1',
            (device_id,)
        )
        
        profile = cursor.fetchone()
        
        # If no default profile exists, get the most recently updated profile
        if not profile:
            cursor.execute(
                'SELECT * FROM watering_profiles WHERE device_id = ? ORDER BY updated_at DESC LIMIT 1',
                (device_id,)
            )
            profile = cursor.fetchone()
        
        conn.close()
        
        # If we still don't have a profile, return default values
        if not profile:
            return {
                'name': 'Default',
                'watering_duration': DEFAULT_WATERING_DURATION,
                'wicking_wait_time': DEFAULT_WICKING_WAIT_TIME,
                'max_daily_cycles': DEFAULT_MAX_DAILY_CYCLES,
                'sensing_interval': DEFAULT_SENSING_INTERVAL,
                'reservoir_limit': None,
                'reservoir_volume': None,
                'max_watering_per_day': None
            }
        
        # Cache the profile
        profile_dict = dict(profile)
        device_profiles[device_id] = profile_dict
        return profile_dict
    
    except Exception as e:
        print(f"Error getting device profile: {str(e)}")
        # Return default values on error
        return {
            'name': 'Default',
            'watering_duration': DEFAULT_WATERING_DURATION,
            'wicking_wait_time': DEFAULT_WICKING_WAIT_TIME,
            'max_daily_cycles': DEFAULT_MAX_DAILY_CYCLES,
            'sensing_interval': DEFAULT_SENSING_INTERVAL,
            'reservoir_limit': None,
            'reservoir_volume': None,
            'max_watering_per_day': None
        }

def refresh_device_profile(device_id):
    """Force refresh the cached profile for a device."""
    if device_id in device_profiles:
        del device_profiles[device_id]
    return get_device_profile(device_id)

def can_water_device(device_id, current_time=None):
    """Check if it's safe to water the device based on timing rules."""
    if current_time is None:
        current_time = time.time()
    
    # Get device profile
    profile = get_device_profile(device_id)
    
    # Initialize tracking for new devices
    if device_id not in last_watering_times:
        last_watering_times[device_id] = 0
    if device_id not in daily_cycles:
        daily_cycles[device_id] = 0
    if device_id not in last_cycle_reset:
        last_cycle_reset[device_id] = current_time
    if device_id not in manual_override:
        manual_override[device_id] = False
    
    # Reset daily cycles and manual override at midnight
    current_date = datetime.datetime.fromtimestamp(current_time).date()
    last_reset_date = datetime.datetime.fromtimestamp(last_cycle_reset[device_id]).date()
    
    if current_date != last_reset_date:
        daily_cycles[device_id] = 0
        manual_override[device_id] = False  # Reset manual override at midnight
        last_cycle_reset[device_id] = current_time
    
    # Check timing rules
    time_since_last_water = current_time - last_watering_times[device_id]
    
    # Apply profile rules
    max_daily_cycles = profile['max_daily_cycles']
    wicking_wait_time = profile['wicking_wait_time']
    
    # Calculate amount of water used today
    water_used_today = daily_cycles[device_id] * (profile['watering_duration'] / 60)  # in minutes
    
    # Check if we're about to exceed reservoir limits
    if profile['max_watering_per_day'] and water_used_today >= profile['max_watering_per_day']:
        print(f"Cannot water: Maximum daily watering limit reached ({water_used_today} minutes)")
        return False
    
    return (time_since_last_water >= wicking_wait_time and 
            daily_cycles[device_id] < max_daily_cycles)

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
        
        # Initialize watering state for new devices
        current_time = time.time()
        if device_id not in last_watering_times:
            last_watering_times[device_id] = current_time - DEFAULT_WICKING_WAIT_TIME  # Allow immediate watering
            daily_cycles[device_id] = 0
            last_cycle_reset[device_id] = current_time
        
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
        print(f"Error in receive_sensor_data: {str(e)}")
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
        
        # Call internal function with is_manual=True
        control_valve_internal(device_id, state, is_manual=True)
        
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
        
        # Pagination parameters
        page = int(request.args.get('page', 1))  # Default to page 1
        limit = int(request.args.get('limit', 100))  # Default to 100 records per page
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        # Calculate timestamp for filtering
        timestamp = datetime.datetime.now() - datetime.timedelta(days=days)
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the total count first for pagination metadata
        cursor.execute(
            '''SELECT COUNT(*) FROM valve_actions 
               WHERE device_id = ? AND timestamp >= ?''',
            (device_id, timestamp_str)
        )
        total_count = cursor.fetchone()[0]
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Get paginated data
        cursor.execute(
            '''SELECT * FROM valve_actions 
               WHERE device_id = ? AND timestamp >= ? 
               ORDER BY timestamp DESC
               LIMIT ? OFFSET ?''',
            (device_id, timestamp_str, limit, offset)
        )
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        
        # Add pagination metadata
        pagination = {
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': math.ceil(total_count / limit) if limit > 0 else 1,
        }
        
        return jsonify({
            'data': result,
            'pagination': pagination
        }), 200
    except Exception as e:
        app.logger.error(f"Error retrieving valve history: {str(e)}")
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
        print(f"\nChecking automation rules for device {device_id}")
        print(f"Current moisture level: {moisture:.1f}%")
        
        # Get device profile
        profile = get_device_profile(device_id)
        
        # Check for manual override
        if device_id in manual_override and manual_override[device_id]:
            print("Manual override is active - skipping automation")
            return
        
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
            print(f"Found active automation rule:")
            print(f"- Low threshold: {rule['low_threshold']}%")
            print(f"- High threshold: {rule['high_threshold']}%")
            print(f"- Using profile: {profile['name']}")
            
            current_time = time.time()
            
            if moisture <= rule['low_threshold']:
                print(f"Moisture ({moisture:.1f}%) is below low threshold ({rule['low_threshold']}%)")
                # Only water if timing rules allow
                if can_water_device(device_id, current_time):
                    print("Starting watering cycle...")
                    # Start watering cycle
                    control_valve_internal(device_id, 1, is_manual=False)
                    
                    # Schedule valve turn off after watering duration from profile
                    def turn_off_valve():
                        time.sleep(profile['watering_duration'])
                        print(f"Watering cycle complete for device {device_id}")
                        control_valve_internal(device_id, 0, is_manual=False)
                        update_watering_state(device_id)
                    
                    # Start timer thread
                    timer_thread = threading.Thread(target=turn_off_valve)
                    timer_thread.daemon = True
                    timer_thread.start()
                else:
                    print("Cannot water due to timing rules:")
                    print(f"- Time since last water: {(current_time - last_watering_times[device_id]) / 60:.1f} minutes")
                    print(f"- Daily cycles used: {daily_cycles[device_id]} of {profile['max_daily_cycles']}")
            
            elif moisture >= rule['high_threshold']:
                print(f"Moisture ({moisture:.1f}%) is above high threshold ({rule['high_threshold']}%)")
                print("Turning valve OFF")
                # Turn off valve if moisture is high enough
                control_valve_internal(device_id, 0, is_manual=False)
            else:
                print(f"Moisture ({moisture:.1f}%) is within normal range ({rule['low_threshold']}% - {rule['high_threshold']}%)")
        else:
            print("No active automation rule found for this device")
    
    except Exception as e:
        print(f"Error in automation: {str(e)}")

def control_valve_internal(device_id, state, is_manual=False):
    """Internal function to control valve and log action."""
    try:
        print(f"\nControlling valve for device {device_id}: {'ON' if state else 'OFF'} (Manual: {is_manual})")
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
        print(f"Command queued: {device_commands[device_id]}")
    except Exception as e:
        print(f"Error controlling valve: {str(e)}")

@app.route('/api/automation/control', methods=['POST'])
def control_automation():
    """Endpoint to enable/disable automation."""
    try:
        data = request.json
        print(f"\nReceived automation control request: {data}")  # Debug log
        
        if not data or 'device_id' not in data or 'enabled' not in data:
            print("Invalid data format")  # Debug log
            return jsonify({'error': 'Invalid data format'}), 400
        
        device_id = data['device_id']
        enabled = int(data['enabled'])  # 0 for disabled, 1 for enabled
        print(f"Setting automation for device {device_id} to: {'enabled' if enabled else 'disabled'}")  # Debug log
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update automation state
        cursor.execute(
            'UPDATE automation_rules SET enabled = ? WHERE device_id = ?',
            (enabled, device_id)
        )
        
        if cursor.rowcount == 0:
            print(f"No existing rule found for device {device_id}, creating new rule")  # Debug log
            # If no rule exists, create one with default values
            cursor.execute(
                '''INSERT INTO automation_rules 
                   (device_id, enabled, low_threshold, high_threshold) 
                   VALUES (?, ?, 30.0, 70.0)''',
                (device_id, enabled)
            )
        
        conn.commit()
        
        # Verify the change
        cursor.execute(
            'SELECT enabled FROM automation_rules WHERE device_id = ?',
            (device_id,)
        )
        result = cursor.fetchone()
        current_state = result[0] if result else None
        print(f"Verified automation state: {current_state}")  # Debug log
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'enabled': current_state
        }), 200
    except Exception as e:
        print(f"Error in control_automation: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

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
                # Get device profile for sensing interval
                profile = get_device_profile(device_id)
                sensing_interval = profile.get('sensing_interval', DEFAULT_SENSING_INTERVAL)
                
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
        
        # Sleep for minimum sensing interval (we'll check each device's specific interval)
        time.sleep(60)  # Check every minute

# Start automation worker thread
automation_thread = threading.Thread(target=automation_worker)
automation_thread.daemon = True
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
        notes = data.get('notes')
        fertilized = data.get('fertilized', False)
        pruned = data.get('pruned', False)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO plant_measurements (
                device_id, plant_name, height, leaf_count, stem_thickness, canopy_width,
                leaf_color, leaf_firmness, notes, fertilized, pruned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_id, plant_name, height, leaf_count, stem_thickness, canopy_width,
            leaf_color, leaf_firmness, notes, fertilized, pruned
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

@app.route('/api/measurements/<int:measurement_id>', methods=['PUT', 'DELETE', 'GET', 'OPTIONS'])
def handle_measurement(measurement_id):
    """Handle all operations for a specific measurement."""
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 204
        
    elif request.method == 'DELETE':
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if measurement exists
            cursor.execute('SELECT id FROM plant_measurements WHERE id = ?', (measurement_id,))
            if not cursor.fetchone():
                if 'conn' in locals():
                    conn.close()
                return jsonify({'error': 'Measurement not found'}), 404
                
            # Delete associated photos first
            cursor.execute('SELECT file_path FROM plant_photos WHERE measurement_id = ?', (measurement_id,))
            photos = cursor.fetchall()
            
            # Delete photo files
            for photo in photos:
                try:
                    if os.path.exists(photo[0]):
                        os.remove(photo[0])
                except Exception as e:
                    print(f"Error deleting photo file: {str(e)}")
            
            # Delete the measurement and associated photos (cascade delete will handle photos table)
            cursor.execute('DELETE FROM plant_measurements WHERE id = ?', (measurement_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'status': 'success', 'message': 'Measurement deleted'}), 200
            
        except Exception as e:
            print(f"Error deleting measurement: {str(e)}")
            if 'conn' in locals():
                conn.close()
            return jsonify({'error': 'Internal server error'}), 500
            
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            # Get the existing measurement
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM plant_measurements WHERE id = ?', (measurement_id,))
            existing = cursor.fetchone()
            
            if not existing:
                return jsonify({'error': 'Measurement not found'}), 404

            # Update the measurement
            update_fields = []
            update_values = []
            
            # Only update fields that are provided
            if 'plant_name' in data:
                update_fields.append('plant_name = ?')
                update_values.append(data['plant_name'])
            if 'height' in data:
                update_fields.append('height = ?')
                update_values.append(data['height'])
            if 'leaf_count' in data:
                update_fields.append('leaf_count = ?')
                update_values.append(data['leaf_count'])
            if 'stem_thickness' in data:
                update_fields.append('stem_thickness = ?')
                update_values.append(data['stem_thickness'])
            if 'canopy_width' in data:
                update_fields.append('canopy_width = ?')
                update_values.append(data['canopy_width'])
            if 'leaf_color' in data:
                update_fields.append('leaf_color = ?')
                update_values.append(data['leaf_color'])
            if 'leaf_firmness' in data:
                update_fields.append('leaf_firmness = ?')
                update_values.append(data['leaf_firmness'])
            if 'notes' in data:
                update_fields.append('notes = ?')
                update_values.append(data['notes'])
            if 'fertilized' in data:
                update_fields.append('fertilized = ?')
                update_values.append(1 if data['fertilized'] else 0)
            if 'pruned' in data:
                update_fields.append('pruned = ?')
                update_values.append(1 if data['pruned'] else 0)
                
            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400
                
            # Add measurement_id to values for WHERE clause
            update_values.append(measurement_id)
            
            # Construct and execute update query
            query = f'''
                UPDATE plant_measurements 
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            cursor.execute(query, update_values)
            conn.commit()
            
            # Return updated measurement
            cursor.execute('SELECT * FROM plant_measurements WHERE id = ?', (measurement_id,))
            updated = cursor.fetchone()
            
            return jsonify({
                'id': updated[0],
                'device_id': updated[1],
                'timestamp': updated[2],
                'plant_name': updated[3],
                'height': updated[4],
                'leaf_count': updated[5],
                'stem_thickness': updated[6],
                'canopy_width': updated[7],
                'leaf_color': updated[8],
                'leaf_firmness': updated[9],
                'notes': updated[10],
                'fertilized': bool(updated[11]),
                'pruned': bool(updated[12])
            })
            
        except Exception as e:
            print(f"Error updating measurement: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/measurements/<int:measurement_id>/photos', methods=['POST'])
def upload_photo(measurement_id):
    """Upload a photo for a specific measurement."""
    try:
        # Check if measurement exists
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM plant_measurements WHERE id = ?', (measurement_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Measurement not found'}), 404

        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400

        photo = request.files['photo']
        if photo.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if photo and allowed_file(photo.filename):
            # Secure the filename and create unique filename
            filename = secure_filename(photo.filename)
            base_name, extension = os.path.splitext(filename)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{base_name}_{timestamp}{extension}"
            
            # Save the file
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            photo.save(file_path)
            
            # Store file info in database
            cursor.execute('''
                INSERT INTO plant_photos (measurement_id, filename, file_path)
                VALUES (?, ?, ?)
            ''', (measurement_id, unique_filename, file_path))
            
            conn.commit()
            photo_id = cursor.lastrowid
            conn.close()
            
            return jsonify({
                'status': 'success',
                'id': photo_id,
                'filename': unique_filename
            }), 200
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        print(f"Error uploading photo: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/measurements/<int:measurement_id>/photos', methods=['GET'])
def get_photos(measurement_id):
    """Get all photos for a specific measurement."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, timestamp 
            FROM plant_photos 
            WHERE measurement_id = ?
            ORDER BY timestamp DESC
        ''', (measurement_id,))
        
        rows = cursor.fetchall()
        photos = [dict(row) for row in rows]
        conn.close()
        
        return jsonify(photos), 200
        
    except Exception as e:
        print(f"Error getting photos: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/photos/<int:photo_id>', methods=['GET'])
def get_photo(photo_id):
    """Get a specific photo by ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path FROM plant_photos WHERE id = ?', (photo_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Photo not found'}), 404
            
        return send_file(result[0], mimetype='image/jpeg')
        
    except Exception as e:
        print(f"Error retrieving photo: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/photos/<int:photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """Delete a specific photo."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get file path before deleting record
        cursor.execute('SELECT file_path FROM plant_photos WHERE id = ?', (photo_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Photo not found'}), 404
            
        file_path = result[0]
        
        # Delete database record
        cursor.execute('DELETE FROM plant_photos WHERE id = ?', (photo_id,))
        conn.commit()
        conn.close()
        
        # Delete actual file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({'status': 'success', 'message': 'Photo deleted'}), 200
        
    except Exception as e:
        print(f"Error deleting photo: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/plants/<device_id>/<plant_name>', methods=['DELETE', 'OPTIONS'])
def delete_plant(device_id, plant_name):
    """Delete all measurements for a specific plant."""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all measurements for this plant
        cursor.execute('''
            SELECT id FROM plant_measurements 
            WHERE device_id = ? AND plant_name = ?
        ''', (device_id, plant_name))
        measurements = cursor.fetchall()
        
        # Delete photos for each measurement
        for measurement in measurements:
            measurement_id = measurement[0]
            cursor.execute('SELECT file_path FROM plant_photos WHERE measurement_id = ?', (measurement_id,))
            photos = cursor.fetchall()
            
            # Delete photo files
            for photo in photos:
                try:
                    if os.path.exists(photo[0]):
                        os.remove(photo[0])
                except Exception as e:
                    print(f"Error deleting photo file: {str(e)}")
        
        # Delete all measurements for this plant (cascade delete will handle photos)
        cursor.execute('''
            DELETE FROM plant_measurements 
            WHERE device_id = ? AND plant_name = ?
        ''', (device_id, plant_name))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Plant profile {plant_name} deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting plant profile: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/zones', methods=['GET'])
def get_zones():
    """Get all garden zones."""
    try:
        app.logger.info("Handling GET request to /api/zones")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First check if the zones table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='zones'")
        if not cursor.fetchone():
            app.logger.error("Zones table does not exist!")
            return jsonify({'error': 'Zones table not initialized'}), 500
            
            # Get all zones
        cursor.execute('SELECT * FROM zones ORDER BY created_at DESC')
        zones = cursor.fetchall()
        app.logger.info(f"Found {len(zones)} zones")
        
        result = []
        for zone in zones:
            zone_data = {
                'id': zone[0],
                'name': zone[1],
                'description': zone[2],
                'device_id': zone[3],
                'width': zone[4],
                'length': zone[5],
                'created_at': zone[6],
                'updated_at': zone[7]
            }
            
            # Get plants for this zone
            cursor.execute('SELECT * FROM plants WHERE zone_id = ?', (zone[0],))
            plants = cursor.fetchall()
            zone_data['plants'] = [{
                'id': plant[0],
                'name': plant[2],
                'species': plant[3],
                'planting_date': plant[4],
                'position_x': plant[5],
                'position_y': plant[6],
                'notes': plant[7],
                'water_requirements': plant[8]
            } for plant in plants]
            
            result.append(zone_data)
        
        conn.close()
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error in get_zones: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones', methods=['POST'])
def create_zone():
    """Create a new garden zone."""
    try:
        app.logger.info("Handling POST request to /api/zones")
        data = request.json
        app.logger.info(f"Received data: {data}")
        
        required_fields = ['name', 'width', 'length']
        if not all(field in data for field in required_fields):
            app.logger.error("Missing required fields")
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First check if the zones table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='zones'")
        if not cursor.fetchone():
            app.logger.error("Zones table does not exist!")
            return jsonify({'error': 'Zones table not initialized'}), 500
        
        cursor.execute('''
            INSERT INTO zones (name, description, device_id, width, length)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data.get('description'),
            data.get('device_id'),
            data['width'],
            data['length']
        ))
        
        zone_id = cursor.lastrowid
        app.logger.info(f"Created zone with ID: {zone_id}")
        conn.commit()
        conn.close()
        
        return jsonify({'id': zone_id, 'status': 'success'}), 201
    except Exception as e:
        app.logger.error(f"Error in create_zone: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones/<int:zone_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_zone(zone_id):
    """Manage a specific garden zone."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM zones WHERE id = ?', (zone_id,))
            zone = cursor.fetchone()
            
            if not zone:
                return jsonify({'error': 'Zone not found'}), 404
            
            result = {
                'id': zone[0],
                'name': zone[1],
                'description': zone[2],
                'device_id': zone[3],
                'width': zone[4],
                'length': zone[5],
                'created_at': zone[6],
                'updated_at': zone[7]
            }
            
            # Get plants in this zone
            cursor.execute('SELECT * FROM plants WHERE zone_id = ?', (zone_id,))
            plants = cursor.fetchall()
            result['plants'] = [{
                'id': plant[0],
                'name': plant[2],
                'species': plant[3],
                'planting_date': plant[4],
                'position_x': plant[5],
                'position_y': plant[6],
                'notes': plant[7],
                'water_requirements': plant[8]
            } for plant in plants]
            
            return jsonify(result), 200
            
        elif request.method == 'PUT':
            data = request.json
            cursor.execute('''
                UPDATE zones 
                SET name = ?, description = ?, device_id = ?, width = ?, length = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                data['name'],
                data.get('description'),
                data.get('device_id'),
                data['width'],
                data['length'],
                zone_id
            ))
            
        elif request.method == 'DELETE':
            # First delete all plants in the zone
            cursor.execute('DELETE FROM plants WHERE zone_id = ?', (zone_id,))
            # Then delete the zone
            cursor.execute('DELETE FROM zones WHERE id = ?', (zone_id,))
        
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones/<int:zone_id>/plants', methods=['GET', 'POST'])
def manage_zone_plants(zone_id):
    """Manage plants within a zone."""
    try:
        app.logger.info(f"Handling {request.method} request to /api/zones/{zone_id}/plants")
        
        # First check if the database exists
        if not os.path.exists(DB_PATH):
            app.logger.error(f"Database file does not exist at {DB_PATH}")
            return jsonify({'error': 'Database not initialized'}), 500
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if request.method == 'GET':
            app.logger.info(f"Fetching plants for zone {zone_id}")
            
            # Check if plants table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plants'")
            if not cursor.fetchone():
                app.logger.error("Plants table does not exist in database")
                return jsonify({'error': 'Plants table not initialized'}), 500
            
            cursor.execute('SELECT * FROM plants WHERE zone_id = ?', (zone_id,))
            plants = cursor.fetchall()
            
            result = [{
                'id': plant[0],
                'zone_id': plant[1],
                'name': plant[2],
                'species': plant[3],
                'planting_date': plant[4],
                'position_x': plant[5],
                'position_y': plant[6],
                'notes': plant[7],
                'water_requirements': plant[8],
                'created_at': plant[9],
                'updated_at': plant[10]
            } for plant in plants]
            
            app.logger.info(f"Found {len(plants)} plants")
            return jsonify(result), 200
            
        elif request.method == 'POST':
            data = request.json
            app.logger.info(f"Creating new plant in zone {zone_id} with data: {data}")
            
            required_fields = ['name', 'species', 'planting_date', 'position_x', 'position_y']
            if not all(field in data for field in required_fields):
                missing_fields = [field for field in required_fields if field not in data]
                app.logger.error(f"Missing required fields: {missing_fields}")
                return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
            
            # Check if plants table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plants'")
            if not cursor.fetchone():
                app.logger.error("Plants table does not exist in database")
                return jsonify({'error': 'Plants table not initialized'}), 500
            
            # Check if zone exists
            cursor.execute('SELECT id FROM zones WHERE id = ?', (zone_id,))
            if not cursor.fetchone():
                app.logger.error(f"Zone {zone_id} does not exist")
                return jsonify({'error': 'Zone not found'}), 404
            
            try:
                cursor.execute('''
                    INSERT INTO plants (
                        zone_id, name, species, planting_date, 
                        position_x, position_y, notes, water_requirements
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    zone_id,
                    data['name'],
                    data['species'],
                    data['planting_date'],
                    data['position_x'],
                    data['position_y'],
                    data.get('notes'),
                    data.get('water_requirements')
                ))
            except sqlite3.Error as e:
                app.logger.error(f"Database error while inserting plant: {str(e)}")
                return jsonify({'error': f'Database error: {str(e)}'}), 500
            
            plant_id = cursor.lastrowid
            app.logger.info(f"Created plant with ID: {plant_id}")
            
            # Add planting event to history
            try:
                cursor.execute('''
                    INSERT INTO zone_history (
                        zone_id, plant_id, event_type, event_description
                    )
                    VALUES (?, ?, ?, ?)
                ''', (
                    zone_id,
                    plant_id,
                    'planting',
                    f"Planted {data['species']} ({data['name']})"
                ))
            except sqlite3.Error as e:
                app.logger.error(f"Database error while adding history event: {str(e)}")
                # Continue even if history event fails
            
            conn.commit()
            
            # Return the created plant
            cursor.execute('SELECT * FROM plants WHERE id = ?', (plant_id,))
            plant = cursor.fetchone()
            result = {
                'id': plant[0],
                'zone_id': plant[1],
                'name': plant[2],
                'species': plant[3],
                'planting_date': plant[4],
                'position_x': plant[5],
                'position_y': plant[6],
                'notes': plant[7],
                'water_requirements': plant[8],
                'created_at': plant[9],
                'updated_at': plant[10]
            }
            
            conn.close()
            return jsonify(result), 201
            
    except Exception as e:
        app.logger.error(f"Error in manage_zone_plants: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones/<int:zone_id>/history', methods=['GET', 'POST'])
def zone_history(zone_id):
    """Manage zone history and events."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('''
                SELECT h.*, p.name as plant_name 
                FROM zone_history h 
                LEFT JOIN plants p ON h.plant_id = p.id 
                WHERE h.zone_id = ? 
                ORDER BY h.timestamp DESC
            ''', (zone_id,))
            history = cursor.fetchall()
            
            result = [{
                'id': event[0],
                'event_type': event[3],
                'event_description': event[4],
                'timestamp': event[5],
                'plant_name': event[6]
            } for event in history]
            
            return jsonify(result), 200
            
        elif request.method == 'POST':
            data = request.json
            required_fields = ['event_type', 'event_description']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            cursor.execute('''
                INSERT INTO zone_history (
                    zone_id, plant_id, event_type, event_description
                )
                VALUES (?, ?, ?, ?)
            ''', (
                zone_id,
                data.get('plant_id'),
                data['event_type'],
                data['event_description']
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return jsonify({'id': event_id, 'status': 'success'}), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones/<int:zone_id>/plants/<int:plant_id>', methods=['PUT', 'DELETE'])
def manage_plant(zone_id, plant_id):
    """Manage a specific plant."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if plant exists and belongs to the zone
        cursor.execute(
            'SELECT id FROM plants WHERE id = ? AND zone_id = ?',
            (plant_id, zone_id)
        )
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Plant not found'}), 404
        
        if request.method == 'PUT':
            data = request.json
            required_fields = ['name', 'species', 'planting_date', 'position_x', 'position_y']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            cursor.execute('''
                UPDATE plants 
                SET name = ?, species = ?, planting_date = ?, 
                    position_x = ?, position_y = ?, notes = ?, 
                    water_requirements = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND zone_id = ?
            ''', (
                data['name'],
                data['species'],
                data['planting_date'],
                data['position_x'],
                data['position_y'],
                data.get('notes'),
                data.get('water_requirements'),
                plant_id,
                zone_id
            ))
            
            # Add update event to history
            cursor.execute('''
                INSERT INTO zone_history (
                    zone_id, plant_id, event_type, event_description
                )
                VALUES (?, ?, ?, ?)
            ''', (
                zone_id,
                plant_id,
                'update',
                f"Updated {data['species']} ({data['name']})"
            ))
            
            conn.commit()
            
            # Return updated plant
            cursor.execute('SELECT * FROM plants WHERE id = ?', (plant_id,))
            plant = cursor.fetchone()
            result = {
                'id': plant[0],
                'zone_id': plant[1],
                'name': plant[2],
                'species': plant[3],
                'planting_date': plant[4],
                'position_x': plant[5],
                'position_y': plant[6],
                'notes': plant[7],
                'water_requirements': plant[8],
                'created_at': plant[9],
                'updated_at': plant[10]
            }
            
            conn.close()
            return jsonify(result), 200
            
        elif request.method == 'DELETE':
            # Add deletion event to history
            cursor.execute('SELECT name, species FROM plants WHERE id = ?', (plant_id,))
            plant = cursor.fetchone()
            if plant:
                cursor.execute('''
                    INSERT INTO zone_history (
                        zone_id, plant_id, event_type, event_description
                    )
                    VALUES (?, ?, ?, ?)
                ''', (
                    zone_id,
                    plant_id,
                    'deletion',
                    f"Removed {plant[1]} ({plant[0]})"
                ))
            
            # Delete the plant
            cursor.execute('DELETE FROM plants WHERE id = ? AND zone_id = ?', (plant_id, zone_id))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success'}), 200
            
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/profiles', methods=['GET'])
def get_watering_profiles():
    """Endpoint to retrieve all watering profiles for a device."""
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM watering_profiles WHERE device_id = ? ORDER BY updated_at DESC',
            (device_id,)
        )
        
        profiles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # If no profiles exist, return the default values
        if not profiles:
            default_profile = {
                'id': 0,
                'name': 'Default',
                'device_id': device_id,
                'is_default': 1,
                'watering_duration': DEFAULT_WATERING_DURATION,
                'wicking_wait_time': DEFAULT_WICKING_WAIT_TIME,
                'max_daily_cycles': DEFAULT_MAX_DAILY_CYCLES,
                'sensing_interval': DEFAULT_SENSING_INTERVAL,
                'reservoir_limit': None,
                'reservoir_volume': None,
                'max_watering_per_day': None,
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            return jsonify([default_profile]), 200
        
        return jsonify(profiles), 200
    except Exception as e:
        app.logger.error(f"Error getting watering profiles: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profiles/<int:profile_id>', methods=['GET'])
def get_profile(profile_id):
    """Endpoint to retrieve a specific watering profile."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM watering_profiles WHERE id = ?', (profile_id,))
        profile = cursor.fetchone()
        conn.close()
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify(dict(profile)), 200
    except Exception as e:
        app.logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profiles', methods=['POST'])
def create_watering_profile():
    """Endpoint to create a new watering profile."""
    try:
        data = request.json
        if not data or 'device_id' not in data or 'name' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        # Extract values with defaults
        device_id = data['device_id']
        name = data['name']
        is_default = int(data.get('is_default', 0))
        watering_duration = int(data.get('watering_duration', DEFAULT_WATERING_DURATION))
        wicking_wait_time = int(data.get('wicking_wait_time', DEFAULT_WICKING_WAIT_TIME))
        max_daily_cycles = int(data.get('max_daily_cycles', DEFAULT_MAX_DAILY_CYCLES))
        sensing_interval = int(data.get('sensing_interval', DEFAULT_SENSING_INTERVAL))
        
        # Optional parameters
        reservoir_limit = data.get('reservoir_limit')
        reservoir_volume = data.get('reservoir_volume')
        max_watering_per_day = data.get('max_watering_per_day')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # If this is being set as the default, unset any existing defaults
        if is_default:
            cursor.execute(
                'UPDATE watering_profiles SET is_default = 0 WHERE device_id = ?',
                (device_id,)
            )
        
        # Insert new profile
        cursor.execute(
            '''INSERT INTO watering_profiles 
               (name, device_id, is_default, watering_duration, wicking_wait_time, 
                max_daily_cycles, sensing_interval, reservoir_limit, reservoir_volume, 
                max_watering_per_day, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))''',
            (name, device_id, is_default, watering_duration, wicking_wait_time, 
             max_daily_cycles, sensing_interval, reservoir_limit, reservoir_volume, 
             max_watering_per_day)
        )
        
        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Remove from cache to force refresh
        refresh_device_profile(device_id)
        
        return jsonify({
            'id': profile_id,
            'status': 'success',
            'message': 'Profile created successfully'
        }), 201
    except Exception as e:
        app.logger.error(f"Error creating watering profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profiles/<int:profile_id>', methods=['PUT'])
def update_watering_profile(profile_id):
    """Endpoint to update an existing watering profile."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get existing profile to get the device_id
        cursor.execute('SELECT device_id FROM watering_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Profile not found'}), 404
        
        device_id = row[0]
        
        # Handle setting this as default
        if 'is_default' in data and data['is_default']:
            cursor.execute(
                'UPDATE watering_profiles SET is_default = 0 WHERE device_id = ?',
                (device_id,)
            )
        
        # Build update statement dynamically
        fields = []
        params = []
        
        update_fields = [
            'name', 'is_default', 'watering_duration', 'wicking_wait_time',
            'max_daily_cycles', 'sensing_interval', 'reservoir_limit',
            'reservoir_volume', 'max_watering_per_day'
        ]
        
        for field in update_fields:
            if field in data:
                fields.append(f"{field} = ?")
                params.append(data[field])
        
        # Always update the updated_at timestamp
        fields.append("updated_at = datetime('now')")
        
        if not fields:
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(profile_id)
        
        # Execute update
        cursor.execute(
            f"UPDATE watering_profiles SET {', '.join(fields)} WHERE id = ?",
            params
        )
        
        conn.commit()
        conn.close()
        
        # Remove from cache to force refresh
        refresh_device_profile(device_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully'
        }), 200
    except Exception as e:
        app.logger.error(f"Error updating watering profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profiles/<int:profile_id>', methods=['DELETE'])
def delete_watering_profile(profile_id):
    """Endpoint to delete a watering profile."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get device_id before deleting
        cursor.execute('SELECT device_id, is_default FROM watering_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Profile not found'}), 404
        
        device_id, is_default = row
        
        # Delete the profile
        cursor.execute('DELETE FROM watering_profiles WHERE id = ?', (profile_id,))
        
        # If this was the default profile, set another profile as default if available
        if is_default:
            cursor.execute(
                'SELECT id FROM watering_profiles WHERE device_id = ? ORDER BY updated_at DESC LIMIT 1',
                (device_id,)
            )
            new_default = cursor.fetchone()
            if new_default:
                cursor.execute(
                    'UPDATE watering_profiles SET is_default = 1 WHERE id = ?',
                    (new_default[0],)
                )
        
        conn.commit()
        conn.close()
        
        # Remove from cache to force refresh
        refresh_device_profile(device_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Profile deleted successfully'
        }), 200
    except Exception as e:
        app.logger.error(f"Error deleting watering profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profiles/<int:profile_id>/set-default', methods=['POST'])
def set_default_profile(profile_id):
    """Endpoint to set a profile as the default for a device."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get device_id for the profile
        cursor.execute('SELECT device_id FROM watering_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Profile not found'}), 404
        
        device_id = row[0]
        
        # Clear existing defaults
        cursor.execute(
            'UPDATE watering_profiles SET is_default = 0 WHERE device_id = ?',
            (device_id,)
        )
        
        # Set this profile as default
        cursor.execute(
            'UPDATE watering_profiles SET is_default = 1 WHERE id = ?',
            (profile_id,)
        )
        
        conn.commit()
        conn.close()
        
        # Remove from cache to force refresh
        refresh_device_profile(device_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Profile set as default'
        }), 200
    except Exception as e:
        app.logger.error(f"Error setting default profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/valve/state', methods=['POST'])
def update_valve_state():
    data = request.json
    device_id = data.get('device_id')
    valve_state = data.get('state')
    
    # Get the current valve state from the database
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT state FROM valve_states WHERE device_id = ? ORDER BY timestamp DESC LIMIT 1",
        (device_id,)
    )
    current_state = cursor.fetchone()
    
    # Only record if the state has changed
    if current_state is None or current_state[0] != valve_state:
        # Insert the new state
        cursor.execute(
            "INSERT INTO valve_states (device_id, state, timestamp) VALUES (?, ?, ?)",
            (device_id, valve_state, datetime.now().isoformat())
        )
        
        # Purge old records - keep only records from the last 30 days
        retention_days = 30  # Adjust this number as needed
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        cursor.execute(
            "DELETE FROM valve_states WHERE device_id = ? AND timestamp < ?",
            (device_id, cutoff_date)
        )
        
        get_db().commit()
        
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 
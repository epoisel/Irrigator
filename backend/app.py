from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import sqlite3
import os
import datetime
import time
import threading
from werkzeug.utils import secure_filename


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

# Photo upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 
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

def init_db():
    """Initialize the database with required tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create moisture_data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moisture_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        moisture REAL NOT NULL,
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
        high_threshold REAL NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Device command queue
device_commands = {}

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Endpoint to receive sensor data from Pico W devices."""
    try:
        data = request.json
        if not data or 'device_id' not in data or 'moisture' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        device_id = data['device_id']
        moisture = float(data['moisture'])
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO moisture_data (device_id, moisture) VALUES (?, ?)',
            (device_id, moisture)
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
            if moisture <= rule['low_threshold']:
                # Moisture too low, turn valve ON
                control_valve_internal(device_id, 1)
            elif moisture >= rule['high_threshold']:
                # Moisture high enough, turn valve OFF
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 
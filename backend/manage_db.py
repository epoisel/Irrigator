#!/usr/bin/env python3
"""
Database management script for the irrigation control system.
This script provides utilities for managing the SQLite database.
"""

import os
import sys
import sqlite3
import argparse
import csv
from datetime import datetime, timedelta

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'irrigation.db')

def init_db():
    """Initialize the database with required tables."""
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

    # Create zones table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        device_id TEXT,
        width REAL NOT NULL,
        length REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create plants table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        species TEXT NOT NULL,
        planting_date DATE NOT NULL,
        position_x REAL NOT NULL,
        position_y REAL NOT NULL,
        notes TEXT,
        water_requirements TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (zone_id) REFERENCES zones(id)
    )
    ''')

    # Create zone_history table for tracking growth and maintenance
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS zone_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_id INTEGER NOT NULL,
        plant_id INTEGER,
        event_type TEXT NOT NULL,
        event_description TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (zone_id) REFERENCES zones(id),
        FOREIGN KEY (plant_id) REFERENCES plants(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def export_data(table_name, output_file, days=None):
    """Export data from a table to a CSV file."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        print(f"Error: Table {table_name} does not exist.")
        conn.close()
        return False
    
    # Build query
    query = f"SELECT * FROM {table_name}"
    params = []
    
    if days:
        timestamp = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        query += " WHERE timestamp >= ?"
        params.append(timestamp)
    
    query += " ORDER BY timestamp DESC"
    
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get column names
        column_names = [description[0] for description in cursor.description]
        
        # Write to CSV
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(column_names)
            writer.writerows(rows)
        
        print(f"Exported {len(rows)} rows to {output_file}")
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error exporting data: {e}")
        conn.close()
        return False

def purge_data(table_name, days):
    """Purge old data from a table."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        print(f"Error: Table {table_name} does not exist.")
        conn.close()
        return False
    
    # Check if table has timestamp column
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    has_timestamp = any(col[1] == 'timestamp' for col in columns)
    
    if not has_timestamp:
        print(f"Error: Table {table_name} does not have a timestamp column.")
        conn.close()
        return False
    
    # Build query
    timestamp = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    query = f"DELETE FROM {table_name} WHERE timestamp < ?"
    
    try:
        cursor.execute(query, (timestamp,))
        deleted_rows = cursor.rowcount
        conn.commit()
        
        print(f"Purged {deleted_rows} rows from {table_name}")
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error purging data: {e}")
        conn.close()
        return False

def list_devices():
    """List all devices in the database."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get devices from moisture_data
        cursor.execute("SELECT DISTINCT device_id FROM moisture_data")
        moisture_devices = set(row[0] for row in cursor.fetchall())
        
        # Get devices from valve_actions
        cursor.execute("SELECT DISTINCT device_id FROM valve_actions")
        valve_devices = set(row[0] for row in cursor.fetchall())
        
        # Get devices from automation_rules
        cursor.execute("SELECT DISTINCT device_id FROM automation_rules")
        automation_devices = set(row[0] for row in cursor.fetchall())
        
        # Combine all devices
        all_devices = moisture_devices.union(valve_devices).union(automation_devices)
        
        if not all_devices:
            print("No devices found in the database.")
            return True
        
        print("Devices in the database:")
        for device_id in sorted(all_devices):
            print(f"- {device_id}")
            
            # Get device stats
            cursor.execute("SELECT COUNT(*) FROM moisture_data WHERE device_id = ?", (device_id,))
            moisture_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM valve_actions WHERE device_id = ?", (device_id,))
            valve_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT * FROM automation_rules WHERE device_id = ?", (device_id,))
            automation = cursor.fetchone()
            
            print(f"  Moisture readings: {moisture_count}")
            print(f"  Valve actions: {valve_count}")
            
            if automation:
                enabled = "Enabled" if automation[2] == 1 else "Disabled"
                print(f"  Automation: {enabled} (Low: {automation[3]}%, High: {automation[4]}%)")
            else:
                print("  Automation: Not configured")
            
            print()
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error listing devices: {e}")
        conn.close()
        return False

def main():
    parser = argparse.ArgumentParser(description='Irrigation System Database Management')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize the database')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to CSV')
    export_parser.add_argument('table', choices=['moisture_data', 'valve_actions', 'automation_rules'],
                              help='Table to export')
    export_parser.add_argument('output', help='Output CSV file')
    export_parser.add_argument('--days', type=int, help='Export data from the last N days')
    
    # Purge command
    purge_parser = subparsers.add_parser('purge', help='Purge old data')
    purge_parser.add_argument('table', choices=['moisture_data', 'valve_actions'],
                             help='Table to purge data from')
    purge_parser.add_argument('days', type=int, help='Purge data older than N days')
    
    # List devices command
    list_parser = subparsers.add_parser('list-devices', help='List all devices in the database')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_db()
    elif args.command == 'export':
        export_data(args.table, args.output, args.days)
    elif args.command == 'purge':
        purge_data(args.table, args.days)
    elif args.command == 'list-devices':
        list_devices()
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timedelta
import os

# Configuration
DATABASE_PATH = "your_database.db"  # Update with your actual database path
RETENTION_DAYS = 30  # How many days of valve state history to keep

def purge_old_records():
    print(f"Purging valve state records older than {RETENTION_DAYS} days...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Calculate cutoff date
    cutoff_date = (datetime.now() - timedelta(days=RETENTION_DAYS)).isoformat()
    
    # Get count before deletion
    cursor.execute("SELECT COUNT(*) FROM valve_states WHERE timestamp < ?", (cutoff_date,))
    count_before = cursor.fetchone()[0]
    
    # Delete old records
    cursor.execute("DELETE FROM valve_states WHERE timestamp < ?", (cutoff_date,))
    
    # Commit changes
    conn.commit()
    
    print(f"Deleted {count_before} old valve state records.")
    
    # Optimize database
    cursor.execute("VACUUM")
    conn.commit()
    
    conn.close()

if __name__ == "__main__":
    purge_old_records() 
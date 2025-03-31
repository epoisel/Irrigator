#!/bin/bash

# This script sets up a cron job to automatically purge old valve history records

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Make sure the purge script is executable
chmod +x "$SCRIPT_DIR/purge_old_records.sh"

# Path to the purge script (absolute path)
PURGE_SCRIPT="$SCRIPT_DIR/purge_old_records.sh"

# Path to the temporary crontab file
TEMP_CRONTAB="/tmp/temp_crontab.txt"

# Create the cron job entry (run every day at 2:00 AM)
CRON_ENTRY="0 2 * * * $PURGE_SCRIPT >> $SCRIPT_DIR/cron_execution.log 2>&1"

# Check if the cron job already exists
if crontab -l 2>/dev/null | grep -q "$PURGE_SCRIPT"; then
    echo "Cron job already exists. Skipping setup."
else
    # Save existing crontab
    crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "" > "$TEMP_CRONTAB"
    
    # Add our entry
    echo "# Automatically purge old valve history records (added on $(date '+%Y-%m-%d'))" >> "$TEMP_CRONTAB"
    echo "$CRON_ENTRY" >> "$TEMP_CRONTAB"
    
    # Install new crontab
    crontab "$TEMP_CRONTAB"
    
    # Clean up
    rm "$TEMP_CRONTAB"
    
    echo "Cron job added successfully. The purge script will run daily at 2:00 AM."
fi

# Show current crontab for verification
echo ""
echo "Current crontab entries:"
crontab -l 
#!/bin/bash

# Create a cron job to run the purge script daily at 2 AM

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PURGE_SCRIPT="$SCRIPT_DIR/purge_old_valve_records.py"

# Make the script executable
chmod +x "$PURGE_SCRIPT"

# Create a temporary crontab file
crontab -l > temp_crontab 2>/dev/null || echo "" > temp_crontab

# Check if the job already exists
if ! grep -q "$PURGE_SCRIPT" temp_crontab; then
    # Add the job to run at 2 AM every day
    echo "0 2 * * * $PURGE_SCRIPT" >> temp_crontab
    
    # Install the new crontab
    crontab temp_crontab
    echo "Cron job installed to purge old valve records daily at 2 AM."
else
    echo "Cron job already exists."
fi

# Clean up
rm temp_crontab 
#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_SCRIPT="$SCRIPT_DIR/manage_db.py"
LOG_FILE="$SCRIPT_DIR/purge_history.log"

# Number of days to keep valve history records (adjust as needed)
DAYS_TO_KEEP=30

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$1"
}

# Check if database script exists
if [ ! -f "$DB_SCRIPT" ]; then
    log_message "Error: Database management script not found at $DB_SCRIPT"
    exit 1
fi

# Ensure Python environment is activated if using virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    log_message "Activated virtual environment"
fi

# Purge old valve history records
log_message "Starting purge of valve history records older than $DAYS_TO_KEEP days"
python3 "$DB_SCRIPT" purge-valve-history "$DAYS_TO_KEEP"
RESULT=$?

if [ $RESULT -eq 0 ]; then
    log_message "Successfully purged old valve history records"
else
    log_message "Error: Failed to purge old valve history records"
fi

# Optimize database (VACUUM)
log_message "Optimizing database..."
sqlite3 "$SCRIPT_DIR/irrigation.db" "VACUUM;"
VACUUM_RESULT=$?

if [ $VACUUM_RESULT -eq 0 ]; then
    log_message "Successfully optimized database"
else
    log_message "Error: Failed to optimize database"
fi

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    log_message "Deactivated virtual environment"
fi

exit $RESULT 
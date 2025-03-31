#!/bin/bash

# Configuration
PI_IP="192.168.1.65"  # REPLACE THIS with your Raspberry Pi's actual IP address
PI_USER="epois"
PI_HOST="$PI_USER@$PI_IP"
REMOTE_DIR="/home/$PI_USER/pico_irrigator"
BACKEND_DIR="backend"

echo "Deploying to Raspberry Pi at $PI_IP..."

# Ensure the remote directory exists
ssh $PI_HOST "mkdir -p $REMOTE_DIR"

# Copy backend files
echo "Copying backend files..."
scp $BACKEND_DIR/app.py $PI_HOST:$REMOTE_DIR/
scp $BACKEND_DIR/manage_db.py $PI_HOST:$REMOTE_DIR/
scp $BACKEND_DIR/requirements.txt $PI_HOST:$REMOTE_DIR/
scp $BACKEND_DIR/pico-irrigator-backend.service $PI_HOST:$REMOTE_DIR/
scp $BACKEND_DIR/purge_old_records.sh $PI_HOST:$REMOTE_DIR/
scp $BACKEND_DIR/setup_cron_job.sh $PI_HOST:$REMOTE_DIR/

# Install dependencies and setup service
echo "Installing dependencies and setting up service..."
ssh $PI_HOST << EOF
    cd ~/pico_irrigator
    # Create virtual environment if it doesn't exist
    python3 -m venv venv || true
    source venv/bin/activate
    # Install/upgrade pip
    pip install --upgrade pip
    # Install requirements
    pip install -r requirements.txt
    # Make scripts executable
    chmod +x purge_old_records.sh
    chmod +x setup_cron_job.sh
    # Setup cron job for automated maintenance
    ./setup_cron_job.sh
    # Setup service
    sudo cp pico-irrigator-backend.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl restart pico-irrigator-backend.service
    sudo systemctl enable pico-irrigator-backend.service
    # Show service status
    sudo systemctl status pico-irrigator-backend.service
EOF

echo "Deployment complete!" 
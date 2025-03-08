#!/bin/bash

# Irrigation Control System Installation Script
# This script sets up the backend and frontend components

echo "=== Irrigation Control System Installation ==="
echo "This script will install and configure the irrigation control system."
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Get the current directory
INSTALL_DIR=$(pwd)
echo "Installing in: $INSTALL_DIR"
echo

# Create installation directory
echo "Creating installation directory..."
mkdir -p /opt/irrigation-system
cp -r $INSTALL_DIR/* /opt/irrigation-system/
cd /opt/irrigation-system

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nodejs npm

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
cd frontend
npm install
npm run build
cd ..

# Set up systemd service
echo "Setting up systemd service..."
cp backend/irrigation-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable irrigation-api
systemctl start irrigation-api

# Create frontend service
cat > /etc/systemd/system/irrigation-frontend.service << EOF
[Unit]
Description=Irrigation Control System Frontend
After=network.target

[Service]
User=pi
WorkingDirectory=/opt/irrigation-system/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=irrigation-frontend
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# Enable and start frontend service
systemctl daemon-reload
systemctl enable irrigation-frontend
systemctl start irrigation-frontend

echo
echo "=== Installation Complete ==="
echo "Backend API running at: http://localhost:5000"
echo "Frontend running at: http://localhost:3000"
echo
echo "To configure the Pico W:"
echo "1. Edit the pico/config.py file with your WiFi and server settings"
echo "2. Upload main.py and config.py to your Pico W"
echo
echo "For more information, see the README.md file." 
# Configuration
$PI_HOST = "epois@raspberrypi.local"
$REMOTE_DIR = "/home/epois/pico_irrigator"
$BACKEND_DIR = "backend"

Write-Host "Deploying to Raspberry Pi..."

# Ensure the remote directory exists
ssh $PI_HOST "mkdir -p $REMOTE_DIR"

# Copy backend files
Write-Host "Copying backend files..."
scp "$BACKEND_DIR/app.py" "${PI_HOST}:$REMOTE_DIR/"
scp "$BACKEND_DIR/manage_db.py" "${PI_HOST}:$REMOTE_DIR/"
scp "$BACKEND_DIR/requirements.txt" "${PI_HOST}:$REMOTE_DIR/"
scp "$BACKEND_DIR/pico-irrigator-backend.service" "${PI_HOST}:$REMOTE_DIR/"

# Install dependencies and setup service
Write-Host "Installing dependencies and setting up service..."

# Use heredoc format for remote commands
ssh $PI_HOST @'
cd /home/epois/pico_irrigator
# Create virtual environment if it doesn't exist
python3 -m venv venv || true
source venv/bin/activate
# Install/upgrade pip
pip install --upgrade pip
# Install requirements
pip install -r requirements.txt
# Setup service
sudo cp pico-irrigator-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart pico-irrigator-backend.service
sudo systemctl enable pico-irrigator-backend.service
# Show service status
sudo systemctl status pico-irrigator-backend.service | cat
'@

Write-Host "Deployment complete!" 
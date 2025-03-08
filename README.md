# Irrigation Control System

A complete irrigation control system using a Raspberry Pi 4 as the backend server and a Raspberry Pi Pico W as the microcontroller for sensor reading and valve control.

## System Overview

This system provides automated irrigation control based on soil moisture readings. It consists of three main components:

1. **Pico W Microcontroller**: Reads moisture sensor data and controls the irrigation valve
2. **Raspberry Pi 4 Backend**: Provides a REST API for data storage and automation logic
3. **Next.js Frontend**: User interface for monitoring and controlling the system

## Features

- Real-time moisture level monitoring
- Manual valve control
- Automated irrigation based on moisture thresholds
- Historical data visualization
- Configurable automation settings
- Responsive web interface

## Directory Structure

```
irrigation-system/
├── backend/                # Flask API backend
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── irrigation-api.service  # Systemd service file
│   └── simulate_data.py    # Data simulation script for testing
│
├── frontend/               # Next.js frontend
│   ├── app/                # Next.js app directory
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── page.tsx        # Main page
│   │   └── ...
│   ├── package.json        # Node.js dependencies
│   └── ...
│
└── pico/                   # Pico W MicroPython code
    ├── main.py             # Main Pico W application
    └── config.py           # Configuration file
```

## Hardware Requirements

- Raspberry Pi 4 (2GB+ RAM recommended)
- Raspberry Pi Pico W
- Soil moisture sensor (analog output)
- Solenoid valve (12V DC recommended)
- Relay module (for controlling the valve)
- Power supply for Raspberry Pi 4 (5V)
- Power supply for valve (12V DC)
- Jumper wires and breadboard

## Wiring Diagram

### Pico W Connections

- **GP26** (ADC0): Connect to moisture sensor output
- **GP16**: Connect to relay module input
- **GND**: Connect to common ground
- **VSYS**: Connect to 5V power supply

### Valve Connections

- Connect the valve to the relay module output
- Connect the valve power supply to the relay module

## Raspberry Pi Installation Guide

### 1. Initial Setup

1. Connect to your Raspberry Pi via SSH:
   ```bash
   ssh pi@your-raspberry-pi-ip
   ```

2. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv nodejs npm git
   ```

### 2. Clone and Setup

1. Clone the repository:
   ```bash
   cd ~
   git clone https://github.com/yourusername/pico_irrigator.git
   cd pico_irrigator
   ```

2. Set up the backend:
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

### 3. Configure the Services

1. Create the backend service:
   ```bash
   sudo nano /etc/systemd/system/pico-irrigator-backend.service
   ```
   
   Add this content:
   ```ini
   [Unit]
   Description=Pico Irrigator Backend Service
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/pico_irrigator/backend
   Environment="PATH=/home/pi/pico_irrigator/backend/venv/bin"
   ExecStart=/home/pi/pico_irrigator/backend/venv/bin/python app.py

   [Install]
   WantedBy=multi-user.target
   ```

2. Create the frontend service:
   ```bash
   sudo nano /etc/systemd/system/pico-irrigator-frontend.service
   ```
   
   Add this content:
   ```ini
   [Unit]
   Description=Pico Irrigator Frontend Service
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/pico_irrigator/frontend
   Environment=NODE_ENV=production
   Environment=PORT=3000
   ExecStart=/usr/bin/npm start

   [Install]
   WantedBy=multi-user.target
   ```

3. Configure environment variables:
   ```bash
   cd ~/pico_irrigator/frontend
   nano .env.local
   ```
   
   Add this content (replace with your Raspberry Pi's IP):
   ```
   NEXT_PUBLIC_API_URL=http://your-raspberry-pi-ip:5000
   NEXT_PUBLIC_DEFAULT_DEVICE_ID=pico_01
   ```

### 4. Start the Services

1. Enable and start the services:
   ```bash
   sudo systemctl enable pico-irrigator-backend
   sudo systemctl start pico-irrigator-backend
   sudo systemctl enable pico-irrigator-frontend
   sudo systemctl start pico-irrigator-frontend
   ```

2. Check service status:
   ```bash
   sudo systemctl status pico-irrigator-backend
   sudo systemctl status pico-irrigator-frontend
   ```

### 5. Access the Application

1. Find your Raspberry Pi's IP address:
   ```bash
   hostname -I
   ```

2. Access the web interface:
   - Open a web browser
   - Go to `http://your-raspberry-pi-ip:3000`

### Troubleshooting

1. Check service logs:
   ```bash
   sudo journalctl -u pico-irrigator-backend -f
   sudo journalctl -u pico-irrigator-frontend -f
   ```

2. Check service status:
   ```bash
   sudo systemctl status pico-irrigator-backend
   sudo systemctl status pico-irrigator-frontend
   ```

3. Common issues:
   - If services fail to start, check logs for errors
   - Make sure all dependencies are installed
   - Verify file permissions
   - Ensure ports 3000 and 5000 are not in use
   - Check firewall settings:
     ```bash
     sudo ufw allow 3000
     sudo ufw allow 5000
     ```

### Updating the Application

To update the application:

1. Pull latest changes:
   ```bash
   cd ~/pico_irrigator
   git pull
   ```

2. Update backend:
   ```bash
   source venv/bin/activate
   pip install -r backend/requirements.txt
   sudo systemctl restart pico-irrigator-backend
   ```

3. Update frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   sudo systemctl restart pico-irrigator-frontend
   ```

## Usage

1. Access the web interface at `http://your-raspberry-pi-ip:3000`

2. The dashboard shows:
   - Current moisture level
   - Valve control button
   - Moisture trend chart
   - Valve activity history
   - Automation settings

3. Configure automation settings:
   - Enable/disable automation
   - Set low moisture threshold (when to turn valve ON)
   - Set high moisture threshold (when to turn valve OFF)

## Testing

You can use the simulation script to test the system without actual hardware:

```
cd backend
python simulate_data.py --device-id pico_sim_01 --interval 5
```

## Troubleshooting

- **Pico W not connecting**: Check WiFi credentials in `config.py`
- **No data in dashboard**: Ensure the backend service is running
- **Valve not responding**: Check relay connections and power supply

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [Next.js](https://nextjs.org/)
- [Chart.js](https://www.chartjs.org/)
- [MicroPython](https://micropython.org/) 
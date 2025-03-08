#!/bin/bash

# Irrigation Control System Development Setup Script
# This script sets up the development environment for the irrigation control system

echo "=== Irrigation Control System Development Setup ==="
echo "This script will set up the development environment for the irrigation control system."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install npm and try again."
    exit 1
fi

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install Pico deployment dependencies
echo "Installing Pico deployment dependencies..."
pip install -r pico/requirements-deploy.txt

# Initialize the database
echo "Initializing the database..."
python backend/manage_db.py init

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Create .env.local file
echo "Creating .env.local file..."
cp frontend/.env.local.example frontend/.env.local

echo
echo "=== Development Setup Complete ==="
echo
echo "To start the backend server:"
echo "  source venv/bin/activate"
echo "  cd backend"
echo "  python app.py"
echo
echo "To start the frontend server:"
echo "  cd frontend"
echo "  npm run dev"
echo
echo "To simulate a device:"
echo "  source venv/bin/activate"
echo "  cd backend"
echo "  python simulate_data.py"
echo
echo "To deploy code to a Pico W:"
echo "  source venv/bin/activate"
echo "  cd pico"
echo "  python deploy_pico.py"
echo
echo "For more information, see the README.md file." 
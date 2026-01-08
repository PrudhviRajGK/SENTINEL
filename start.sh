#!/bin/bash

echo "╔══════════════════════════════════════════╗"
echo "║   Sentinel - Enterprise Threat Intel    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Starting Sentinel..."
echo ""

# Check if Python backend dependencies are installed
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Check if React dependencies are installed
if [ ! -d "sentinel-frontend/node_modules" ]; then
    echo "Installing React dependencies..."
    cd sentinel-frontend
    npm install
    cd ..
fi

# Start Flask backend in background
echo ""
echo "Starting Flask backend on http://localhost:5000..."
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start React frontend
echo "Starting React frontend on http://localhost:3000..."
cd sentinel-frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          Sentinel is running!            ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Backend:  http://localhost:5000         ║"
echo "║  Frontend: http://localhost:3000         ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Press CTRL+C to stop all services"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

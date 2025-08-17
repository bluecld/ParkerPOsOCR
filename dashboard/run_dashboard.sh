#!/bin/sh

# Simple Dashboard Starter
DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"

# Kill any existing dashboard processes
pkill -f "python.*app.py" 2>/dev/null

# Wait a moment
sleep 2

# Start dashboard in background
cd "$DASHBOARD_DIR"
nohup python3 app.py > dashboard.log 2>&1 &

echo "Dashboard started in background (PID: $!)"
echo "Log file: $DASHBOARD_DIR/dashboard.log"
echo "To stop: pkill -f 'python.*app.py'"

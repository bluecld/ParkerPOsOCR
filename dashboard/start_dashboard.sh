#!/bin/sh

# PO Dashboard Auto-Restart Script
# This script runs the Dashboard and automatically restarts it if it crashes

DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
LOG_FILE="/volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log"
PIDFILE="/var/run/po-dashboard.pid"

cd "$DASHBOARD_DIR"

# Function to start the dashboard
start_dashboard() {
    echo "[$(date)] Starting PO Dashboard..." >> "$LOG_FILE"
    
    # Kill any existing dashboard processes
    pkill -f "python.*app.py"
    sleep 2
    
    # Start the dashboard in background
    nohup python3 app.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PIDFILE"
    
    echo "[$(date)] Dashboard started with PID $(cat $PIDFILE)" >> "$LOG_FILE"
}

# Function to check if dashboard is running
is_running() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Running
        fi
    fi
    return 1  # Not running
}

# Main monitoring loop
echo "[$(date)] Starting Dashboard Monitor..." >> "$LOG_FILE"

while true; do
    if ! is_running; then
        echo "[$(date)] Dashboard not running, starting..." >> "$LOG_FILE"
        start_dashboard
    fi
    
    # Check every 30 seconds
    sleep 30
done

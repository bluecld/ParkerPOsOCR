#!/bin/sh

# PO Processing Dashboard Startup Script
# This script starts the Flask dashboard in the background with auto-restart

DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
PIDFILE="/var/run/po-dashboard.pid"
LOGFILE="/volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log"

start_dashboard() {
    echo "Starting PO Processing Dashboard..."
    
    # Check if already running
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Dashboard is already running (PID: $PID)"
            return 0
        else
            echo "Removing stale PID file"
            rm -f "$PIDFILE"
        fi
    fi
    
    # Start the dashboard
    cd "$DASHBOARD_DIR"
    nohup python3 app.py >> "$LOGFILE" 2>&1 &
    PID=$!
    echo $PID > "$PIDFILE"
    echo "Dashboard started with PID: $PID"
    echo "Logs: $LOGFILE"
}

stop_dashboard() {
    echo "Stopping PO Processing Dashboard..."
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "Dashboard stopped (PID: $PID)"
        else
            echo "Dashboard was not running"
        fi
        rm -f "$PIDFILE"
    else
        echo "PID file not found"
        # Kill any python3 app.py processes just in case
        pkill -f "python3 app.py"
    fi
}

restart_dashboard() {
    stop_dashboard
    sleep 2
    start_dashboard
}

status_dashboard() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Dashboard is running (PID: $PID)"
            echo "Access at: http://192.168.0.62:5000"
            echo "Logs: $LOGFILE"
        else
            echo "Dashboard is not running (stale PID file)"
            rm -f "$PIDFILE"
        fi
    else
        echo "Dashboard is not running"
    fi
}

case "$1" in
    start)
        start_dashboard
        ;;
    stop)
        stop_dashboard
        ;;
    restart)
        restart_dashboard
        ;;
    status)
        status_dashboard
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

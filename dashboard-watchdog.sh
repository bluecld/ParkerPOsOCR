#!/bin/sh

# Dashboard Watchdog Script
# This script monitors the dashboard and restarts it if it crashes

SERVICE_SCRIPT="/volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh"
PIDFILE="/var/run/po-dashboard.pid"

# Check if dashboard is running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "$(date): Dashboard crashed, restarting..."
        $SERVICE_SCRIPT restart
    fi
else
    echo "$(date): Dashboard not running, starting..."
    $SERVICE_SCRIPT start
fi

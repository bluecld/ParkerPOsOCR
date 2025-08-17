#!/bin/bash

# Secure Dashboard Watchdog - Self-Healing Monitor
# This script monitors the dashboard and restarts it if it fails

DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
PID_FILE="$DASHBOARD_DIR/dashboard_secure.pid"
WATCHDOG_LOG="$DASHBOARD_DIR/logs/watchdog.log"
SERVICE_SCRIPT="$DASHBOARD_DIR/dashboard_secure_service.sh"
SERVICE_NAME="po-dashboard-secure"

# Create logs directory
mkdir -p "$DASHBOARD_DIR/logs"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$WATCHDOG_LOG"
}

# Function to check if dashboard is responsive
check_dashboard_health() {
    # Test if the dashboard responds to HTTPS requests on port 8443
    if curl -k -s --connect-timeout 5 https://localhost:8443/login > /dev/null 2>&1; then
        return 0  # Healthy
    else
        return 1  # Unhealthy
    fi
}

# Function to check if process is running
check_service_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Running
        else
            return 1  # Not running
        fi
    else
        return 1  # No PID file
    fi
}

# Main monitoring logic
log_message "🔍 Watchdog: Checking dashboard health..."

# Check if service is running
if check_service_running; then
    PID=$(cat "$PID_FILE")
    log_message "✅ Service active (PID: $PID)"
    
    if check_dashboard_health; then
        log_message "✅ Dashboard responding correctly"
        # Clean exit - everything is healthy
        exit 0
    else
        log_message "❌ Dashboard not responding - restarting service..."
        sh "$SERVICE_SCRIPT" stop
        sleep 3
        sh "$SERVICE_SCRIPT" start
        log_message "🔄 Dashboard restart attempted via service script"
    fi
else
    log_message "❌ Service not running - starting..."
    sh "$SERVICE_SCRIPT" start
    log_message "🚀 Dashboard start attempted via service script"
fi

# Verify restart was successful
sleep 10
if check_dashboard_health; then
    log_message "✅ Dashboard is now healthy"
else
    log_message "🚨 Dashboard restart failed - manual intervention needed"
    log_message "Service status: $(sh $SERVICE_SCRIPT status)"
fi

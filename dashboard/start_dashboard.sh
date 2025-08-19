#!/bin/sh

# PO Dashboard Auto-Restart Script with Enhanced Self-Healing
# This script runs the Dashboard and automatically restarts it if it crashes

DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
LOG_FILE="/volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log"
PIDFILE="/var/run/po-dashboard.pid"

cd "$DASHBOARD_DIR"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to start the dashboard
start_dashboard() {
    log_message "Starting PO Dashboard..."
    
    # Kill any existing dashboard processes
    pkill -f "python.*app.py" 2>/dev/null
    pkill -f "python.*app_secure.py" 2>/dev/null
    sleep 3
    
    # Check if secure app exists, prefer it over regular app
    if [ -f "app_secure.py" ]; then
        log_message "Starting secure dashboard (HTTPS)"
        nohup python3 app_secure.py >> "$LOG_FILE" 2>&1 &
    else
        log_message "Starting regular dashboard (HTTP)"
        nohup python3 app.py >> "$LOG_FILE" 2>&1 &
    fi
    
    echo $! > "$PIDFILE"
    log_message "Dashboard started with PID $(cat $PIDFILE)"
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

# Function to check if dashboard is responsive
is_responsive() {
    # Try HTTPS first (port 9443), then HTTP (port 5000)
    if curl -k -s --connect-timeout 5 https://localhost:9443/api/health > /dev/null 2>&1; then
        return 0  # Responsive
    elif curl -s --connect-timeout 5 http://localhost:5000/api/health > /dev/null 2>&1; then
        return 0  # Responsive
    else
        return 1  # Not responsive
    fi
}

# Function to perform health check
health_check() {
    if is_running; then
        if is_responsive; then
            return 0  # Healthy
        else
            log_message "⚠️ Dashboard running but not responsive"
            return 1  # Unhealthy
        fi
    else
        log_message "❌ Dashboard not running"
        return 1  # Unhealthy
    fi
}

# Main monitoring loop with enhanced self-healing
log_message "🚀 Starting Enhanced Dashboard Monitor with Self-Healing"

consecutive_failures=0
max_consecutive_failures=3

while true; do
    if health_check; then
        if [ "$consecutive_failures" -gt 0 ]; then
            log_message "✅ Dashboard recovered - resetting failure counter"
            consecutive_failures=0
        fi
    else
        consecutive_failures=$((consecutive_failures + 1))
        log_message "⚠️ Health check failed (attempt $consecutive_failures/$max_consecutive_failures)"
        
        if [ "$consecutive_failures" -ge "$max_consecutive_failures" ]; then
            log_message "🚨 Multiple failures detected - forcing restart"
            start_dashboard
            consecutive_failures=0
            sleep 10  # Give extra time after forced restart
        fi
    fi
    
    # Check every 30 seconds
    sleep 30
done

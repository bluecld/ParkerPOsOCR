#!/bin/bash

# Secure Dashboard Auto-Start Script
# This script ensures the dashboard starts on boot and sets up monitoring

DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
SERVICE_SCRIPT="$DASHBOARD_DIR/dashboard_secure_service.sh"
WATCHDOG_SCRIPT="$DASHBOARD_DIR/dashboard_watchdog.sh"
STARTUP_LOG="$DASHBOARD_DIR/logs/startup.log"

# Create logs directory
mkdir -p "$DASHBOARD_DIR/logs"

# Function to log with timestamp
log_startup() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$STARTUP_LOG"
}

log_startup "🚀 Auto-start: Initializing secure dashboard startup..."

# Wait for system to be ready
sleep 30

# Start the dashboard service
log_startup "🔐 Starting secure dashboard service..."
cd "$DASHBOARD_DIR"
sh "$SERVICE_SCRIPT" start

# Wait for startup
sleep 10

# Verify it's running (check secure dashboard port)
if curl -k -s --connect-timeout 10 https://localhost:8443/login > /dev/null 2>&1; then
    log_startup "✅ Secure dashboard started successfully and is responding"
else
    log_startup "⚠️ Secure dashboard may not be fully ready yet - watchdog will monitor"
fi

# Set up cron job for watchdog monitoring (every 2 minutes for better responsiveness)
CRON_JOB="*/2 * * * * sh $WATCHDOG_SCRIPT >/dev/null 2>&1"

# Check if cron job already exists
if ! (crontab -l 2>/dev/null | grep -q dashboard_watchdog.sh); then
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    log_startup "✅ Watchdog monitoring enabled (every 2 minutes)"
else
    log_startup "✅ Watchdog monitoring already configured"
fi

log_startup "🎯 Auto-start complete - dashboard is self-monitoring"

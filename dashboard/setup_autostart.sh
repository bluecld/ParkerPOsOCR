#!/bin/bash

# Auto-start Dashboard Setup Script
# This script sets up automatic dashboard startup

DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
CRON_JOB="@reboot $DASHBOARD_DIR/dashboard_service.sh start"

echo "🚀 Parker Dashboard Auto-Start Setup"
echo "===================================="

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -F "$DASHBOARD_DIR/dashboard_service.sh" >/dev/null; then
    echo "✅ Auto-start cron job already exists"
else
    echo "📅 Adding auto-start cron job..."
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    if [ $? -eq 0 ]; then
        echo "✅ Auto-start cron job added successfully"
    else
        echo "❌ Failed to add cron job"
        exit 1
    fi
fi

# Also add a health check cron job (every 5 minutes)
HEALTH_CHECK="*/5 * * * * $DASHBOARD_DIR/dashboard_service.sh status >/dev/null || $DASHBOARD_DIR/dashboard_service.sh start"

if crontab -l 2>/dev/null | grep -F "dashboard_service.sh status" >/dev/null; then
    echo "✅ Health check cron job already exists"
else
    echo "🏥 Adding health check cron job..."
    (crontab -l 2>/dev/null; echo "$HEALTH_CHECK") | crontab -
    echo "✅ Health check cron job added (checks every 5 minutes)"
fi

echo ""
echo "📋 Current cron jobs for dashboard:"
crontab -l | grep dashboard_service.sh

echo ""
echo "🎯 Setup Complete!"
echo "=================="
echo "✅ Dashboard will auto-start after NAS reboot"
echo "✅ Health check will restart dashboard if it stops"
echo "✅ Check every 5 minutes to ensure dashboard stays running"
echo ""
echo "Manual commands:"
echo "  Start:   $DASHBOARD_DIR/dashboard_service.sh start"
echo "  Stop:    $DASHBOARD_DIR/dashboard_service.sh stop"
echo "  Status:  $DASHBOARD_DIR/dashboard_service.sh status"
echo ""

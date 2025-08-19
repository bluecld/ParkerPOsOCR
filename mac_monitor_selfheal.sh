#!/bin/bash
# Mac PDF Monitor Self-Healing Enhancement
# This script enhances the existing Mac folder watch to print function with self-healing
# It does NOT replace the existing functionality, only adds monitoring and recovery

MAC_HOST="192.168.0.105"
MAC_USER="Anthony"
SCRIPT_DIR="/Users/Shared/ParkerPOsOCR"
MONITOR_SCRIPT="pdf_auto_print_monitor.py"
LOG_FILE="$SCRIPT_DIR/self_healing.log"

# Function to log messages (Mac compatible)
log_mac_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to check if Mac PDF monitor is running
check_mac_pdf_monitor() {
    ssh -o ConnectTimeout=10 -o BatchMode=yes "$MAC_USER@$MAC_HOST" "
        # Check if monitor process is running
        if ps aux | grep -v grep | grep -q '$MONITOR_SCRIPT'; then
            echo 'RUNNING'
        else
            echo 'STOPPED'
        fi
    " 2>/dev/null
}

# Function to check LaunchAgent status
check_launch_agent() {
    ssh -o ConnectTimeout=10 -o BatchMode=yes "$MAC_USER@$MAC_HOST" "
        # Check LaunchAgent status
        if launchctl list | grep -q 'com.parkerpos.pdf.autoprint'; then
            echo 'LOADED'
        else
            echo 'UNLOADED'
        fi
    " 2>/dev/null
}

# Function to restart Mac PDF monitor
restart_mac_pdf_monitor() {
    echo "Attempting to restart Mac PDF monitor..."
    
    ssh -o ConnectTimeout=15 -o BatchMode=yes "$MAC_USER@$MAC_HOST" "
        cd $SCRIPT_DIR
        
        # Log the restart attempt
        echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Self-healing restart attempt\" >> self_healing.log
        
        # Stop any existing monitor processes
        pkill -f '$MONITOR_SCRIPT' 2>/dev/null || true
        
        # Restart LaunchAgent
        launchctl unload ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist 2>/dev/null || true
        sleep 2
        launchctl load ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist 2>/dev/null || true
        launchctl start com.parkerpos.pdf.autoprint 2>/dev/null || true
        
        sleep 5
        
        # Verify restart
        if ps aux | grep -v grep | grep -q '$MONITOR_SCRIPT'; then
            echo \"\$(date '+%Y-%m-%d %H:%M:%S') - ✅ Monitor restarted successfully\" >> self_healing.log
            echo 'RESTART_SUCCESS'
        else
            echo \"\$(date '+%Y-%m-%d %H:%M:%S') - ❌ Monitor restart failed\" >> self_healing.log
            echo 'RESTART_FAILED'
        fi
    " 2>/dev/null
}

# Function to perform Mac system health check
mac_health_check() {
    echo "🔍 Checking Mac PDF monitoring system..."
    
    # Check SSH connectivity
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$MAC_USER@$MAC_HOST" "echo 'SSH OK'" >/dev/null 2>&1; then
        echo "❌ SSH connection to Mac failed"
        return 1
    fi
    
    echo "✅ SSH connection to Mac: OK"
    
    # Check PDF monitor process
    monitor_status=$(check_mac_pdf_monitor)
    if [ "$monitor_status" = "RUNNING" ]; then
        echo "✅ PDF monitor process: RUNNING"
    else
        echo "⚠️ PDF monitor process: STOPPED"
        return 1
    fi
    
    # Check LaunchAgent
    agent_status=$(check_launch_agent)
    if [ "$agent_status" = "LOADED" ]; then
        echo "✅ LaunchAgent: LOADED"
    else
        echo "⚠️ LaunchAgent: UNLOADED"
        return 1
    fi
    
    # Check export directory exists
    if ssh -o ConnectTimeout=5 -o BatchMode=yes "$MAC_USER@$MAC_HOST" "test -d $SCRIPT_DIR/exports" 2>/dev/null; then
        echo "✅ Export directory: EXISTS"
    else
        echo "⚠️ Export directory: MISSING"
        return 1
    fi
    
    echo "🎯 Mac PDF monitoring system: HEALTHY"
    return 0
}

# Function to install self-healing cron job on Mac
install_mac_self_healing() {
    echo "Installing Mac self-healing monitoring..."
    
    # Create self-healing script on Mac
    ssh -o ConnectTimeout=15 "$MAC_USER@$MAC_HOST" "
        cat > $SCRIPT_DIR/mac_self_heal.sh << 'HEAL_EOF'
#!/bin/bash
# Mac PDF Monitor Self-Healing Script (runs locally on Mac)

SCRIPT_DIR=\"/Users/Shared/ParkerPOsOCR\"
MONITOR_SCRIPT=\"pdf_auto_print_monitor.py\"
LOG_FILE=\"\$SCRIPT_DIR/self_healing.log\"

# Function to check if monitor is running
check_monitor() {
    if ps aux | grep -v grep | grep -q \"\$MONITOR_SCRIPT\"; then
        return 0
    else
        return 1
    fi
}

# Function to restart monitor
restart_monitor() {
    echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Self-healing: Monitor stopped, restarting...\" >> \"\$LOG_FILE\"
    
    # Kill existing processes
    pkill -f \"\$MONITOR_SCRIPT\" 2>/dev/null || true
    
    # Restart LaunchAgent
    launchctl unload ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist 2>/dev/null || true
    sleep 2
    launchctl load ~/Library/LaunchAgents/com.parkerpos.pdf.autoprint.plist 2>/dev/null || true
    launchctl start com.parkerpos.pdf.autoprint 2>/dev/null || true
    
    sleep 3
    
    if check_monitor; then
        echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Self-healing: ✅ Monitor restarted successfully\" >> \"\$LOG_FILE\"
    else
        echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Self-healing: ❌ Monitor restart failed\" >> \"\$LOG_FILE\"
    fi
}

# Main check
if ! check_monitor; then
    restart_monitor
fi
HEAL_EOF

        chmod +x \$SCRIPT_DIR/mac_self_heal.sh
        
        # Add cron job for self-healing (every 10 minutes)
        CRON_JOB=\"*/10 * * * * \$SCRIPT_DIR/mac_self_heal.sh >/dev/null 2>&1\"
        
        # Check if cron job exists
        if ! (crontab -l 2>/dev/null | grep -q mac_self_heal.sh); then
            (crontab -l 2>/dev/null; echo \"\$CRON_JOB\") | crontab -
            echo \"✅ Mac self-healing cron job installed (every 10 minutes)\"
        else
            echo \"✅ Mac self-healing already configured\"
        fi
        
        echo \"🎯 Mac self-healing monitoring configured!\"
    "
}

# Function to check Mac system status
mac_system_status() {
    echo "📊 Mac PDF Monitoring System Status"
    echo "===================================="
    
    if mac_health_check; then
        echo ""
        echo "📈 Additional Mac System Info:"
        
        # Get process details
        ssh -o ConnectTimeout=10 -o BatchMode=yes "$MAC_USER@$MAC_HOST" "
            echo \"📊 Process Details:\"
            ps aux | grep -v grep | grep '$MONITOR_SCRIPT' | head -1 | awk '{print \"  PID: \" \$2 \", CPU: \" \$3 \"%, Memory: \" \$4 \"%\"}'
            
            echo \"\"
            echo \"📁 Directory Status:\"
            echo \"  Exports: \$(ls -1 $SCRIPT_DIR/exports/ 2>/dev/null | wc -l) files\"
            echo \"  Printed: \$(ls -1 $SCRIPT_DIR/exports/printed/ 2>/dev/null | wc -l) files\"
            
            echo \"\"
            echo \"📄 Recent Print Activity:\"
            if [ -f $SCRIPT_DIR/print_log.txt ]; then
                tail -3 $SCRIPT_DIR/print_log.txt | sed 's/^/  /'
            else
                echo \"  No print log found\"
            fi
        " 2>/dev/null
    fi
}

# Main script logic
case "${1:-check}" in
    "check")
        mac_health_check
        ;;
    "restart")
        restart_result=$(restart_mac_pdf_monitor)
        if [ "$restart_result" = "RESTART_SUCCESS" ]; then
            echo "✅ Mac PDF monitor restarted successfully"
        else
            echo "❌ Failed to restart Mac PDF monitor"
        fi
        ;;
    "install-healing")
        install_mac_self_healing
        ;;
    "status")
        mac_system_status
        ;;
    *)
        echo "Mac PDF Monitor Self-Healing Tool"
        echo "================================="
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  check           - Check Mac PDF monitor health"
        echo "  restart         - Restart Mac PDF monitor"
        echo "  install-healing - Install self-healing on Mac"
        echo "  status          - Show detailed Mac system status"
        echo ""
        echo "Examples:"
        echo "  $0 check                # Check if Mac monitor is healthy"
        echo "  $0 install-healing      # Setup automatic Mac self-healing"
        echo "  $0 status               # Show detailed Mac system status"
        echo ""
        echo "Note: This script enhances but does not replace existing Mac functionality"
        ;;
esac

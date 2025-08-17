#!/bin/bash

# PO System Health Monitor
# Usage: ./monitor_po_system.sh [check|watch|repair]

DOCKER_DIR="/volume1/Main/Main/ParkerPOsOCR/docker_system"
CONTAINER_NAME="po-processor"
LOG_FILE="/volume1/Main/Main/ParkerPOsOCR/monitor.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

check_container() {
    if docker ps | grep -q "$CONTAINER_NAME"; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

check_docker_daemon() {
    if docker info >/dev/null 2>&1; then
        return 0  # Docker is running
    else
        return 1  # Docker is not running
    fi
}

repair_system() {
    log_message "Attempting to repair PO system..."
    
    # Check if Docker daemon is running
    if ! check_docker_daemon; then
        log_message "ERROR: Docker daemon is not running. Cannot repair automatically."
        return 1
    fi
    
    # Try to start the container
    cd "$DOCKER_DIR"
    if docker-compose up -d >/dev/null 2>&1; then
        log_message "Container restart attempted"
        sleep 5
        
        if check_container; then
            log_message "SUCCESS: Container is now running"
            return 0
        else
            log_message "FAILED: Container still not running after restart attempt"
            return 1
        fi
    else
        log_message "ERROR: Failed to run docker-compose up"
        return 1
    fi
}

single_check() {
    if check_docker_daemon; then
        if check_container; then
            log_message "STATUS: PO System is running normally"
            echo "✅ PO System is healthy"
        else
            log_message "WARNING: Container is not running"
            echo "❌ Container is DOWN"
            
            if [ "$1" = "auto-repair" ]; then
                repair_system
            else
                echo "Run with 'repair' option to attempt automatic fix"
            fi
        fi
    else
        log_message "ERROR: Docker daemon is not running"
        echo "❌ Docker daemon is DOWN"
    fi
}

watch_mode() {
    log_message "Starting continuous monitoring (Ctrl+C to stop)"
    echo "🔍 Monitoring PO System (checking every 2 minutes)..."
    echo "📝 Log file: $LOG_FILE"
    
    while true; do
        if ! check_docker_daemon; then
            log_message "CRITICAL: Docker daemon is down"
            echo "❌ $(date '+%H:%M:%S') Docker daemon DOWN"
        elif ! check_container; then
            log_message "WARNING: PO Container is down - attempting repair"
            echo "⚠️  $(date '+%H:%M:%S') Container DOWN - repairing..."
            
            if repair_system; then
                echo "✅ $(date '+%H:%M:%S') Container restored"
            else
                echo "❌ $(date '+%H:%M:%S') Repair failed"
            fi
        else
            echo "✅ $(date '+%H:%M:%S') System healthy"
        fi
        
        sleep 120  # Check every 2 minutes
    done
}

case "${1:-check}" in
    "check")
        single_check
        ;;
    "watch")
        watch_mode
        ;;
    "repair")
        single_check auto-repair
        ;;
    "status")
        echo "PO System Health Status:"
        echo "======================="
        
        if check_docker_daemon; then
            echo "Docker Daemon: ✅ Running"
            
            if check_container; then
                echo "PO Container: ✅ Running"
                
                # Check recent activity
                if [ -f "/volume1/Main/Main/ParkerPOsOCR/POs/po_processor.log" ]; then
                    last_activity=$(tail -1 /volume1/Main/Main/ParkerPOsOCR/POs/po_processor.log | cut -d' ' -f1-2)
                    echo "Last Activity: $last_activity"
                fi
                
                # Check file counts
                scan_count=$(ls -1 /volume1/Main/Main/ParkerPOsOCR/Scans/ 2>/dev/null | wc -l)
                echo "Files in Scans: $scan_count"
                
            else
                echo "PO Container: ❌ Not Running"
            fi
        else
            echo "Docker Daemon: ❌ Not Running"
        fi
        ;;
    "help"|"--help")
        echo "PO System Health Monitor"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  check     Quick health check"
        echo "  status    Detailed status report"
        echo "  repair    Check and repair if needed"
        echo "  watch     Continuous monitoring mode"
        echo "  help      Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 check     # Quick check"
        echo "  $0 repair    # Fix issues automatically"
        echo "  $0 watch     # Monitor continuously"
        echo ""
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

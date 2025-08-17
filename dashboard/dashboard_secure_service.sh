#!/bin/bash

# Secure Dashboard Service Manager
DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
PID_FILE="$DASHBOARD_DIR/dashboard_secure.pid"
LOG_FILE="$DASHBOARD_DIR/logs/dashboard_secure.log"
APP_FILE="$DASHBOARD_DIR/app_secure.py"
PORT=8443

# Create logs directory
mkdir -p "$DASHBOARD_DIR/logs"

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "🔐 Secure dashboard is already running (PID: $PID)"
                exit 1
            else
                echo "🧹 Removing stale PID file"
                rm -f "$PID_FILE"
            fi
        fi
        
        echo "🚀 Starting secure dashboard..."
        cd "$DASHBOARD_DIR"
        nohup python3 "$APP_FILE" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "✅ Secure dashboard started (PID: $(cat $PID_FILE))"
        echo "🔗 Access at: https://your-nas-ip:5000"
        echo "📝 Logs: $LOG_FILE"
        ;;
    
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "🛑 Stopping secure dashboard (PID: $PID)..."
                kill "$PID"
                rm -f "$PID_FILE"
                echo "✅ Secure dashboard stopped"
            else
                echo "❌ Dashboard not running (PID $PID not found)"
                rm -f "$PID_FILE"
            fi
        else
            echo "❌ Dashboard not running (no PID file)"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Secure dashboard is running (PID: $PID)"
                echo "🔗 Access at: https://your-nas-ip:5000"
                # Show recent log entries
                if [ -f "$LOG_FILE" ]; then
                    echo "📝 Recent log entries:"
                    tail -n 5 "$LOG_FILE"
                fi
            else
                echo "❌ Dashboard not running (PID $PID not found)"
                rm -f "$PID_FILE"
            fi
        else
            echo "❌ Secure dashboard is not running"
        fi
        ;;
    
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📝 Dashboard logs (last 50 lines):"
            tail -n 50 "$LOG_FILE"
        else
            echo "❌ No log file found"
        fi
        ;;
    
    security)
        SECURITY_LOG="$DASHBOARD_DIR/logs/security.log"
        if [ -f "$SECURITY_LOG" ]; then
            echo "🔐 Security logs (last 20 lines):"
            tail -n 20 "$SECURITY_LOG"
        else
            echo "❌ No security log file found"
        fi
        ;;
    
    *)
        echo "🔐 Secure Parker PO Dashboard Service Manager"
        echo "Usage: $0 {start|stop|restart|status|logs|security}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the secure dashboard"
        echo "  stop     - Stop the secure dashboard"
        echo "  restart  - Restart the secure dashboard"
        echo "  status   - Check dashboard status"
        echo "  logs     - View dashboard logs"
        echo "  security - View security logs"
        exit 1
        ;;
esac

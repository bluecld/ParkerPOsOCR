#!/bin/bash

# Persistent Dashboard Service Manager
# Usage: ./dashboard_service.sh {start|stop|restart|status|logs}

DASHBOARD_DIR="/volume1/Main/Main/ParkerPOsOCR/dashboard"
PID_FILE="$DASHBOARD_DIR/dashboard.pid"
LOG_FILE="$DASHBOARD_DIR/logs/dashboard.log"
PORT=5000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if dashboard is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PID_FILE"  # Stale PID file
            return 1  # Not running
        fi
    else
        return 1  # Not running
    fi
}

# Start dashboard service
start_dashboard() {
    print_status "Starting Parker Dashboard Service..."
    
    if is_running; then
        print_warning "Dashboard is already running (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    # Ensure logs directory exists
    mkdir -p "$DASHBOARD_DIR/logs"
    
    # Navigate to dashboard directory
    cd "$DASHBOARD_DIR" || {
        print_error "Cannot access dashboard directory: $DASHBOARD_DIR"
        return 1
    }
    
    # Check if required packages are installed
    if ! python3 -c "import flask, docker, psutil" 2>/dev/null; then
        print_status "Installing required packages..."
        pip3 install flask docker psutil gunicorn --quiet
    fi
    
    # Start dashboard in background with nohup
    print_status "Starting dashboard server on port $PORT..."
    
    nohup python3 -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app import app
app.run(host='0.0.0.0', port=$PORT, debug=False)
" > "$LOG_FILE" 2>&1 & echo $! > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 3
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "Dashboard started successfully (PID: $pid)"
        print_success "Access URL: http://$(hostname -I | awk '{print $1}'):$PORT"
        return 0
    else
        print_error "Failed to start dashboard"
        return 1
    fi
}

# Stop dashboard service
stop_dashboard() {
    print_status "Stopping Parker Dashboard Service..."
    
    if ! is_running; then
        print_warning "Dashboard is not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    print_status "Stopping dashboard (PID: $pid)..."
    
    # Try graceful shutdown first
    kill "$pid" 2>/dev/null
    
    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "Forcing dashboard shutdown..."
        kill -9 "$pid" 2>/dev/null
    fi
    
    rm -f "$PID_FILE"
    print_success "Dashboard stopped"
}

# Restart dashboard service
restart_dashboard() {
    print_status "Restarting Parker Dashboard Service..."
    stop_dashboard
    sleep 2
    start_dashboard
}

# Show dashboard status
show_status() {
    print_status "Parker Dashboard Service Status:"
    echo "=================================="
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "Dashboard is running (PID: $pid)"
        
        # Check if port is accessible
        if netstat -tulpn 2>/dev/null | grep -q ":$PORT "; then
            print_success "Port $PORT is listening"
        else
            print_warning "Port $PORT may not be accessible"
        fi
        
        # Show URL
        local ip=$(hostname -I | awk '{print $1}')
        echo "Access URL: http://$ip:$PORT"
        
        # Show process info
        echo ""
        echo "Process Information:"
        ps -p "$pid" -o pid,ppid,cmd,%cpu,%mem,etime 2>/dev/null || print_warning "Cannot get process info"
        
    else
        print_error "Dashboard is not running"
    fi
    
    echo ""
    echo "Log file: $LOG_FILE"
    echo "PID file: $PID_FILE"
}

# Show dashboard logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== Dashboard Logs (last 50 lines) ==="
        tail -50 "$LOG_FILE"
    else
        print_warning "No log file found at $LOG_FILE"
    fi
}

# Install as system service (optional)
install_service() {
    print_status "Installing dashboard as system service..."
    
    # Create systemd service file
    cat > /etc/systemd/system/parker-dashboard.service << EOF
[Unit]
Description=Parker PO Dashboard Service
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=$DASHBOARD_DIR
ExecStart=$DASHBOARD_DIR/dashboard_service.sh start
ExecStop=$DASHBOARD_DIR/dashboard_service.sh stop
ExecReload=$DASHBOARD_DIR/dashboard_service.sh restart
PIDFile=$PID_FILE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable parker-dashboard.service
    
    print_success "Service installed! You can now use:"
    echo "  systemctl start parker-dashboard"
    echo "  systemctl stop parker-dashboard"
    echo "  systemctl status parker-dashboard"
}

# Main script logic
case "${1:-status}" in
    "start")
        start_dashboard
        ;;
    "stop")
        stop_dashboard
        ;;
    "restart")
        restart_dashboard
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "install-service")
        install_service
        ;;
    "help"|"--help"|"-h")
        echo "Parker Dashboard Service Manager"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  start           Start the dashboard service"
        echo "  stop            Stop the dashboard service"
        echo "  restart         Restart the dashboard service"
        echo "  status          Show service status"
        echo "  logs            Show recent logs"
        echo "  install-service Install as system service"
        echo "  help            Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 start        # Start dashboard in background"
        echo "  $0 status       # Check if running"
        echo "  $0 logs         # View recent activity"
        echo ""
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

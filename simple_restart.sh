#!/bin/bash

# Simple PO System Restart Script
echo "Parker PO OCR System Control"
echo "=============================="

DOCKER_DIR="/volume1/Main/Main/ParkerPOsOCR/docker_system"

case "$1" in
    start)
        echo "Starting PO system..."
        cd "$DOCKER_DIR"
        docker-compose up -d
        echo "System started. Use 'docker ps' to check status."
        ;;
    stop)
        echo "Stopping PO system..."
        cd "$DOCKER_DIR"
        docker-compose down
        echo "System stopped."
        ;;
    restart)
        echo "Restarting PO system..."
        cd "$DOCKER_DIR"
        docker-compose down
        sleep 2
        docker-compose up -d
        echo "System restarted."
        ;;
    rebuild)
        echo "Rebuilding PO system..."
        cd "$DOCKER_DIR"
        docker-compose down
        docker-compose up --build -d
        echo "System rebuilt and started."
        ;;
    status)
        echo "Container status:"
        docker ps | grep po-processor || echo "Container not running"
        ;;
    logs)
        echo "Showing logs (Ctrl+C to exit):"
        cd "$DOCKER_DIR"
        docker-compose logs -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|rebuild|status|logs}"
        echo ""
        echo "  start   - Start the container"
        echo "  stop    - Stop the container"
        echo "  restart - Quick restart"
        echo "  rebuild - Rebuild and restart"
        echo "  status  - Check if running"
        echo "  logs    - View live logs"
        ;;
esac

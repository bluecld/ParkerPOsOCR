#!/bin/bash

# Parker PO OCR System - Container Restart Script
# Usage: ./restart_po_system.sh [option]
# Options: start, stop, restart, status, logs

set -e

# Configuration
DOCKER_DIR="/volume1/Main/Main/ParkerPOsOCR/docker_system"
CONTAINER_NAME="po-processor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if we're in the right directory
check_directory() {
    if [ ! -f "$DOCKER_DIR/docker-compose.yml" ]; then
        print_error "docker-compose.yml not found in $DOCKER_DIR"
        exit 1
    fi
    cd "$DOCKER_DIR"
}

# Function to show container status
show_status() {
    print_status "Checking container status..."
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "$CONTAINER_NAME"; then
        print_success "Container is running:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}" | grep -E "(NAMES|$CONTAINER_NAME)"
    else
        print_warning "Container is not running"
        # Check if container exists but is stopped
        if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "$CONTAINER_NAME"; then
            print_warning "Container exists but is stopped:"
            docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -E "(NAMES|$CONTAINER_NAME)"
        fi
    fi
}

# Function to start the system
start_system() {
    print_status "Starting PO Processing System..."
    check_directory
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        print_warning "Container is already running"
        return
    fi
    
    docker-compose up -d
    
    # Wait a moment for container to start
    sleep 3
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        print_success "Container started successfully"
        show_status
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Function to stop the system
stop_system() {
    print_status "Stopping PO Processing System..."
    check_directory
    
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        print_warning "Container is not running"
        return
    fi
    
    docker-compose down
    print_success "Container stopped successfully"
}

# Function to restart the system
restart_system() {
    print_status "Restarting PO Processing System..."
    check_directory
    
    print_status "Stopping container..."
    docker-compose down
    
    print_status "Starting container..."
    docker-compose up -d
    
    # Wait a moment for container to start
    sleep 3
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        print_success "Container restarted successfully"
        show_status
    else
        print_error "Failed to restart container"
        exit 1
    fi
}

# Function to rebuild and restart (force update)
rebuild_system() {
    print_status "Rebuilding and restarting PO Processing System..."
    check_directory
    
    print_status "Stopping and removing container..."
    docker-compose down
    
    print_status "Rebuilding container with latest changes..."
    docker-compose up --build -d
    
    # Wait a moment for container to start
    sleep 5
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        print_success "Container rebuilt and started successfully"
        show_status
    else
        print_error "Failed to rebuild container"
        exit 1
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing container logs (press Ctrl+C to exit)..."
    check_directory
    
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        print_warning "Container is not running, showing last logs..."
        docker-compose logs --tail=50
    else
        docker-compose logs -f
    fi
}

# Function to show usage
show_usage() {
    echo "Parker PO OCR System - Container Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the PO processing container"
    echo "  stop      Stop the PO processing container" 
    echo "  restart   Restart the PO processing container"
    echo "  rebuild   Rebuild and restart (use after code changes)"
    echo "  status    Show current container status"
    echo "  logs      Show container logs (real-time)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start           # Start the system"
    echo "  $0 restart         # Quick restart"
    echo "  $0 rebuild         # Rebuild after making changes"
    echo "  $0 status          # Check if running"
    echo "  $0 logs            # Monitor processing"
    echo ""
}

# Main script logic
case "${1:-help}" in
    "start")
        start_system
        ;;
    "stop")
        stop_system
        ;;
    "restart")
        restart_system
        ;;
    "rebuild")
        rebuild_system
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac

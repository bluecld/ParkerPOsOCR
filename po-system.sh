#!/bin/bash

# Simple PO System Management Script
# Replaces all the complex service scripts, watchdogs, and cron jobs

COMPOSE_FILE="/volume1/Main/Main/ParkerPOsOCR/docker-compose-complete.yml"
LOG_FILE="/volume1/Main/Main/ParkerPOsOCR/system-manager.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

case "$1" in
    start)
        log_message "🚀 Starting complete PO system..."
        cd /volume1/Main/Main/ParkerPOsOCR
        docker-compose -f "$COMPOSE_FILE" up -d
        log_message "✅ System started - Dashboard: https://localhost:8443"
        ;;
    
    stop)
        log_message "🛑 Stopping PO system..."
        cd /volume1/Main/Main/ParkerPOsOCR
        docker-compose -f "$COMPOSE_FILE" down
        log_message "✅ System stopped"
        ;;
    
    restart)
        log_message "🔄 Restarting PO system..."
        cd /volume1/Main/Main/ParkerPOsOCR
        docker-compose -f "$COMPOSE_FILE" restart
        log_message "✅ System restarted"
        ;;
    
    status)
        log_message "📊 Checking system status..."
        cd /volume1/Main/Main/ParkerPOsOCR
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    
    logs)
        cd /volume1/Main/Main/ParkerPOsOCR
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=50
        ;;
    
    health)
        log_message "🏥 Checking system health..."
        if curl -k -s --connect-timeout 5 https://localhost:8443/login > /dev/null 2>&1; then
            log_message "✅ Dashboard healthy"
        else
            log_message "❌ Dashboard not responding - restarting..."
            cd /volume1/Main/Main/ParkerPOsOCR
            docker-compose -f "$COMPOSE_FILE" restart dashboard
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|health}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the complete PO system"
        echo "  stop    - Stop the complete PO system"
        echo "  restart - Restart the complete PO system"
        echo "  status  - Show service status"
        echo "  logs    - Follow system logs"
        echo "  health  - Check and heal system health"
        exit 1
        ;;
esac

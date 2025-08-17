#!/bin/sh
# Development debugging toolkit

echo "🐛 ParkerPO Development Debugging Toolkit"
echo "========================================="

case "$1" in
    "api")
        echo "📡 Testing API endpoints..."
        echo "Dashboard health:"
        curl -k -s https://localhost:8443/api/health 2>/dev/null || echo "❌ Health endpoint failed"
        
        echo -e "\nDashboard stats:"
        curl -k -s https://localhost:8443/api/stats 2>/dev/null || echo "❌ Stats endpoint failed"
        ;;
    
    "logs")
        echo "📋 Recent dashboard logs:"
        docker logs po-dashboard --tail 20
        ;;
    
    "files")
        PO_NUM=${2:-"4551241574"}
        echo "📁 Files for PO $PO_NUM:"
        if [ -d "/volume1/Main/Main/ParkerPOsOCR/POs/$PO_NUM" ]; then
            ls -la "/volume1/Main/Main/ParkerPOsOCR/POs/$PO_NUM/"
            echo -e "\n📄 JSON content:"
            cat "/volume1/Main/Main/ParkerPOsOCR/POs/$PO_NUM/${PO_NUM}_info.json" | head -10
        else
            echo "❌ PO directory not found"
        fi
        ;;
    
    "container")
        echo "🐳 Container status:"
        docker ps --filter "name=po-dashboard" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        echo -e "\n🔍 Container details:"
        docker inspect po-dashboard | grep -A 5 -B 5 "IPAddress\|Ports" | head -15
        ;;
    
    "network")
        echo "🌐 Network diagnostics:"
        echo "Port 8443 status:"
        netstat -tlnp | grep :8443
        
        echo -e "\nConnectivity test:"
        curl -k -s -o /dev/null -w "Localhost: %{http_code}\n" https://localhost:8443/login
        curl -k -s -o /dev/null -w "Network: %{http_code}\n" https://192.168.0.62:8443/login
        ;;
    
    "shell")
        echo "🐚 Opening dashboard container shell..."
        docker exec -it po-dashboard bash
        ;;
    
    "restart")
        echo "🔄 Quick restart..."
        ./quick_deploy.sh
        ;;
    
    *)
        echo "Usage: $0 {api|logs|files|container|network|shell|restart} [po_number]"
        echo ""
        echo "Commands:"
        echo "  api        - Test API endpoints"
        echo "  logs       - Show recent logs"
        echo "  files      - Show files for PO (default: 4551241574)"
        echo "  container  - Show container status"
        echo "  network    - Test network connectivity"
        echo "  shell      - Open container shell"
        echo "  restart    - Quick restart dashboard"
        ;;
esac

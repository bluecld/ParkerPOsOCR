#!/bin/sh
# Reliable Dashboard Deployment Script - Optimized for Development
# This ensures changes are properly applied every time

echo "🔄 Starting dashboard deployment process..."

# 1. Navigate to project directory
cd /volume1/Main/Main/ParkerPOsOCR || exit 1

# 2. Stop the dashboard container completely
echo "⏹️  Stopping dashboard container..."
docker-compose -f docker-compose-complete.yml stop dashboard

# 3. Wait for complete shutdown
echo "⏱️  Waiting for clean shutdown..."
sleep 3

# 4. Remove the container to ensure clean state
echo "🗑️  Removing old container..."
docker-compose -f docker-compose-complete.yml rm -f dashboard

# 5. Clear browser cache instructions
echo "📱 Remember to hard refresh your browser:"
echo "   Chrome/Firefox: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)"
echo "   Safari: Cmd+Option+R"

# 6. Rebuild the container (only if code changes were made)
if [ "$1" = "rebuild" ]; then
    echo "🔨 Rebuilding dashboard container..."
    docker-compose -f docker-compose-complete.yml build dashboard --no-cache
fi

# 7. Start the container fresh
echo "🚀 Starting fresh dashboard container..."
docker-compose -f docker-compose-complete.yml up -d dashboard

# 8. Wait for startup and show progress
echo "⏱️  Waiting for dashboard to be ready..."
for i in $(seq 1 15); do
    if docker ps | grep -q "po-dashboard"; then
        echo "   Container started... ($i/15)"
        break
    fi
    sleep 1
done

# 9. Additional wait for Flask app startup
sleep 5

# 10. Check if it's running
echo "✅ Checking dashboard status..."
if docker ps | grep -q "po-dashboard"; then
    echo "✅ Dashboard container is running!"
    echo "🌐 Access at: https://192.168.0.62:9443"
    
    # 11. Test connectivity
    echo "🔍 Testing connectivity..."
    for i in $(seq 1 5); do
        if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:9443/login | grep -q "200"; then
            echo "✅ Dashboard is responding correctly!"
            echo ""
            echo "🎉 DEPLOYMENT SUCCESSFUL!"
            echo "💡 Changes should be visible immediately (hard refresh browser if needed)"
            exit 0
        else
            echo "   Testing connectivity... ($i/5)"
            sleep 2
        fi
    done
    echo "⚠️  Dashboard may not be fully ready yet. Check logs if issues persist:"
    echo "   docker logs po-dashboard --tail 20"
else
    echo "❌ Dashboard failed to start! Check logs:"
    docker logs po-dashboard --tail 20
    exit 1
fi

echo "🏁 Deployment process completed!"

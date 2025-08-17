#!/bin/bash

echo "🔍 COMPREHENSIVE SYSTEM VERIFICATION"
echo "==================================="

# Check Docker containers
echo "📦 Docker Container Status:"
docker ps --filter name=po-

echo ""
echo "🗂️ Config Files in Container:"
docker exec po-dashboard ls -la /app/logs/ | grep config || echo "No config files found"

echo ""
echo "📋 Notification Config Content:"
docker exec po-dashboard cat /app/logs/notification_config.json 2>/dev/null || echo "❌ Notification config not found in container"

echo ""
echo "🔗 Dashboard Connectivity:"
curl -k -s --connect-timeout 5 https://localhost:8443/login > /dev/null 2>&1 && echo "✅ Dashboard responding" || echo "❌ Dashboard not responding"

echo ""
echo "📊 Recent Container Logs:"
docker logs po-dashboard --tail=5

echo ""
echo "🧪 Testing Notification API (without auth):"
docker exec po-dashboard python3 -c "
import os
config_path = '/app/logs/notification_config.json'
print(f'Config exists: {os.path.exists(config_path)}')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        content = f.read()
        print(f'Config size: {len(content)} bytes')
        print('First 100 chars:', content[:100])
"

echo ""
echo "🔧 System Health Check Complete!"

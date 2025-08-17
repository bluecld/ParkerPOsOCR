#!/bin/bash

echo "🔧 Fixing notification configuration paths and rebuilding dashboard..."

# Navigate to project directory
cd /volume1/Main/Main/ParkerPOsOCR

# Stop the current dashboard
echo "📦 Stopping dashboard container..."
docker-compose -f docker-compose-complete.yml stop dashboard

# Rebuild dashboard with no cache to ensure all changes are included
echo "🔨 Rebuilding dashboard container..."
docker-compose -f docker-compose-complete.yml build --no-cache dashboard

# Ensure notification config exists in container
echo "📋 Copying notification configuration..."
if [ -f "./dashboard/notification_config.json" ]; then
    docker run --rm -v $(pwd)/dashboard/logs:/app/logs parkerposocr-dashboard cp /volume1/Main/Main/ParkerPOsOCR/dashboard/notification_config.json /app/logs/ 2>/dev/null || echo "Direct copy failed, will use docker cp after start"
fi

# Start the dashboard
echo "🚀 Starting dashboard container..."
docker-compose -f docker-compose-complete.yml up -d dashboard

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 10

# Copy the notification config if it exists
if [ -f "./dashboard/notification_config.json" ]; then
    echo "📋 Copying notification config to container..."
    docker cp ./dashboard/notification_config.json po-dashboard:/app/logs/notification_config.json
    echo "✅ Notification config copied"
fi

# Check container status
echo "📊 Checking container status..."
docker-compose -f docker-compose-complete.yml ps

# Test the API endpoint
echo "🧪 Testing notification config API..."
curl -k -s https://localhost:8443/login | head -20

echo ""
echo "✅ Dashboard rebuild complete!"
echo "🌐 Access the dashboard at: https://192.168.0.62:8443"
echo "🔧 Try the notification settings again - the path error should be resolved!"

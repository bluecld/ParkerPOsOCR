#!/bin/sh
# Hot-reload development server
# This watches for changes and automatically restarts the dashboard

echo "🔥 Starting hot-reload development server..."

# Function to restart dashboard
restart_dashboard() {
    echo "🔄 Detected changes, restarting dashboard..."
    docker-compose -f docker-compose-complete.yml restart dashboard
    echo "✅ Dashboard restarted!"
}

# Watch for changes in dashboard directory
while true; do
    # Use find to detect file modifications in the last minute
    CHANGED=$(find /volume1/Main/Main/ParkerPOsOCR/dashboard -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" -newer /tmp/last_check 2>/dev/null)
    
    if [ -n "$CHANGED" ]; then
        echo "📝 Changes detected in:"
        echo "$CHANGED"
        restart_dashboard
        # Update timestamp
        touch /tmp/last_check
        sleep 10  # Prevent rapid restarts
    fi
    
    sleep 2
done

#!/bin/sh
# Quick deployment for template/static file changes only
# Use this for HTML, CSS, JS changes that don't require container rebuild

echo "🚀 Quick template deployment..."

cd /volume1/Main/Main/ParkerPOsOCR || exit 1

# Just restart the container (templates are mounted as volumes)
docker-compose -f docker-compose-complete.yml restart dashboard

echo "⏱️  Waiting for restart..."
sleep 8

if docker ps | grep -q "po-dashboard"; then
    echo "✅ Dashboard restarted!"
    echo "🌐 Access at: https://192.168.0.62:9443"
    echo "💡 Hard refresh your browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
else
    echo "❌ Restart failed! Use full deployment script."
fi

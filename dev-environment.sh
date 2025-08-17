# Development Environment Configuration
# Use this for faster development cycles

# Flask Development Settings
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=app_secure.py
export TEMPLATES_AUTO_RELOAD=1

# Python Development
export PYTHONPATH="/volume1/Main/Main/ParkerPOsOCR/dashboard:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Docker Development
export COMPOSE_PROJECT_NAME=parkerposocr_dev
export DOCKER_BUILDKIT=1

# Aliases for faster development
alias dcd='cd /volume1/Main/Main/ParkerPOsOCR'
alias dashboard-logs='docker logs po-dashboard --tail 50 -f'
alias dashboard-shell='docker exec -it po-dashboard bash'
alias dashboard-restart='./quick_deploy.sh'
alias dashboard-rebuild='./deploy_dashboard_changes.sh rebuild'
alias dashboard-test='curl -k -I https://localhost:8443/login'

# Quick commands
alias ll='ls -la'
alias grep='grep --color=auto'

echo "🚀 Development environment loaded!"
echo "💡 Quick commands available:"
echo "   dcd                 - Go to project directory"
echo "   dashboard-logs      - Watch dashboard logs"
echo "   dashboard-shell     - Open shell in dashboard container"
echo "   dashboard-restart   - Quick restart for template changes"
echo "   dashboard-rebuild   - Full rebuild for code changes"
echo "   dashboard-test      - Test dashboard connectivity"

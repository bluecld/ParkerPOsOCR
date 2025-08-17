---
name: "Docker Management Assistant"
description: "Docker container management and deployment guidance for Parker PO OCR System"
author: "Parker PO OCR Team"
version: "1.0"
tags: ["docker", "containers", "deployment", "devops"]
---

# Docker Management Context

You are a Docker specialist for the Parker PO OCR System, focusing on container management, deployment optimization, and containerization best practices.

## Container Architecture

**Current Setup:**
- **po-dashboard**: Flask web application (port 8443)
- **po-processor**: OCR and file processing service
- **Docker Compose**: `docker-compose-complete.yml`

**Key Configuration Files:**
```
docker-compose-complete.yml  # Production configuration
dashboard/Dockerfile         # Dashboard container build
docker_system/Dockerfile     # Processor container build
```

## Container Management Commands

### 🚀 Quick Operations
```bash
# Load shortcuts
source dev-environment.sh

# Quick restart (preserves data)
dashboard-restart

# Full rebuild (fresh start)
dashboard-rebuild

# Monitor logs
dashboard-logs

# System status
docker ps
docker stats
```

### 🔧 Manual Container Operations
```bash
# Stop services
docker-compose -f docker-compose-complete.yml down

# Start services
docker-compose -f docker-compose-complete.yml up -d

# View specific service logs
docker-compose -f docker-compose-complete.yml logs po-dashboard
docker-compose -f docker-compose-complete.yml logs po-processor

# Execute commands in running container
docker exec -it po-dashboard /bin/bash
docker exec -it po-dashboard python3 -c "import flask; print(flask.__version__)"
```

## Development vs Production

**Development Configuration:**
```yaml
# docker-compose-complete.yml - Development section
environment:
  - FLASK_ENV=development
  - TEMPLATES_AUTO_RELOAD=1
  - FLASK_DEBUG=1
volumes:
  - ./dashboard/templates:/app/templates:ro  # Template hot-reload
```

**Production Considerations:**
- Remove debug flags
- Use proper secret management
- Implement health checks
- Configure resource limits
- Set up log rotation

## Common Docker Issues

### 🐳 Container Won't Start
**Symptoms:**
- Container exits immediately
- "Port already in use" errors
- Volume mount failures

**Diagnostic Steps:**
```bash
# Check container status
docker ps -a

# View startup logs
docker logs po-dashboard

# Check port conflicts
lsof -i :8443
netstat -tlnp | grep 8443

# Inspect container configuration
docker inspect po-dashboard
```

**Solutions:**
- Stop conflicting services: `docker stop $(docker ps -q)`
- Remove stuck containers: `docker rm po-dashboard`
- Check volume permissions: `ls -la dashboard/`
- Free up ports: Kill processes using port 8443

### 🔄 Hot-Reload Not Working
**Symptoms:**
- Template changes not reflected
- Need manual restart for changes
- Development feels slow

**Solutions:**
```bash
# Ensure development environment loaded
source dev-environment.sh

# Use hot-reload script
./hot-reload.sh

# Check volume mounts
docker inspect po-dashboard | grep -A 10 Mounts

# Verify Flask configuration
docker exec po-dashboard env | grep FLASK
```

### 📊 Performance Issues
**Symptoms:**
- Slow container startup
- High resource usage
- Container restarts frequently

**Investigation:**
```bash
# Resource usage
docker stats po-dashboard

# Container processes
docker exec po-dashboard ps aux

# System resources
free -m
df -h

# Container logs for errors
docker logs po-dashboard | tail -50
```

**Optimization:**
- Optimize Dockerfile layers
- Use multi-stage builds
- Set resource limits
- Clean up unused images: `docker image prune -f`

## Deployment Workflows

### 🚀 Quick Development Deploy
```bash
# Standard development deployment
./deploy_dashboard_changes.sh

# Manual steps if needed:
docker-compose -f docker-compose-complete.yml down
docker-compose -f docker-compose-complete.yml up -d
debug.sh network  # Verify deployment
```

### 🎯 Production Deployment
```bash
# 1. Backup current state
docker-compose -f docker-compose-complete.yml down
cp -r POs/ POs_backup_$(date +%Y%m%d_%H%M%S)

# 2. Pull latest code
git pull origin main

# 3. Rebuild containers
docker-compose -f docker-compose-complete.yml build --no-cache

# 4. Deploy with health checks
docker-compose -f docker-compose-complete.yml up -d

# 5. Verify deployment
debug.sh network
debug.sh filemaker
```

## Container Optimization

### 📦 Dockerfile Best Practices
```dockerfile
# Multi-stage build example
FROM python:3.11-slim as base
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (leverage Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use non-root user
RUN useradd -m appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f https://localhost:8443/health || exit 1
```

### 🔧 Resource Management
```yaml
# docker-compose.yml resource limits
services:
  po-dashboard:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    restart: unless-stopped
```

## Monitoring and Logging

### 📊 Container Health Monitoring
```bash
# Health status
docker inspect po-dashboard | jq '.[0].State.Health'

# Resource usage over time
docker stats --no-stream po-dashboard

# Container events
docker events --filter container=po-dashboard
```

### 📝 Log Management
```bash
# Configure log rotation in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

# View logs with timestamps
docker logs -t po-dashboard

# Follow logs
docker logs -f po-dashboard

# Export logs
docker logs po-dashboard > dashboard_$(date +%Y%m%d).log
```

## Backup and Recovery

### 💾 Container Backup Strategy
```bash
# Backup volumes
docker run --rm \
  -v parker_po_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/parker_po_backup_$(date +%Y%m%d).tar.gz /data

# Export container configuration
docker inspect po-dashboard > po-dashboard-config.json

# Backup database/files
cp -r POs/ POs_backup_$(date +%Y%m%d_%H%M%S)/
```

### 🔄 Container Recovery
```bash
# Restore from backup
docker run --rm \
  -v parker_po_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/parker_po_backup_YYYYMMDD.tar.gz -C /

# Recreate containers
docker-compose -f docker-compose-complete.yml up -d
```

## Troubleshooting Checklist

**Before Deployment:**
- [ ] Test locally: `docker-compose up`
- [ ] Check resource availability: `free -m && df -h`
- [ ] Verify configuration files exist
- [ ] Backup current data

**After Deployment:**
- [ ] Verify containers running: `docker ps`
- [ ] Test network connectivity: `debug.sh network`
- [ ] Check application logs: `dashboard-logs`
- [ ] Validate FileMaker integration: `debug.sh filemaker`

**If Issues Occur:**
- [ ] Check container logs: `docker logs po-dashboard`
- [ ] Verify port bindings: `netstat -tlnp | grep 8443`
- [ ] Test container health: `docker inspect po-dashboard`
- [ ] Review resource usage: `docker stats`

Remember: Docker containers should be stateless. Always externalize data and configuration. Use proper volume mounts for persistence.

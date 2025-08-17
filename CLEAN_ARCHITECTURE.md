# Parker PO System - Clean Docker Architecture

## 🎯 Overview
A unified Docker Compose solution that eliminates all the startup conflicts and management complexity by running both the PO processing pipeline and secure dashboard as containerized services.

## 🏗️ Architecture

### Services
1. **po-processor**: OCR processing, FileMaker integration, file monitoring
2. **dashboard**: Secure HTTPS dashboard with authentication

### Key Benefits
- ✅ **Single Point of Control**: One Docker Compose file manages everything
- ✅ **Built-in Reliability**: Docker handles restarts automatically with `restart: unless-stopped`
- ✅ **Clean Networking**: Containers communicate via internal network
- ✅ **No Port Conflicts**: Docker manages port allocation and cleanup
- ✅ **Health Monitoring**: Built-in health checks and recovery

## 🚀 Management Commands

### System Control
```bash
# Start the complete system
./po-system.sh start

# Stop everything
./po-system.sh stop

# Restart services
./po-system.sh restart

# Check status
./po-system.sh status

# View logs
./po-system.sh logs

# Health check with auto-recovery
./po-system.sh health
```

### Direct Docker Commands
```bash
# Using Docker Compose directly
cd /volume1/Main/Main/ParkerPOsOCR
docker-compose -f docker-compose-complete.yml up -d
docker-compose -f docker-compose-complete.yml logs -f
docker-compose -f docker-compose-complete.yml ps
```

## 🔧 Configuration

### Environment Variables (Dashboard)
- `USE_HTTPS=true`: Enable HTTPS with self-signed certificates
- `SSL_CERT_PATH=/app/ssl/dashboard.crt`: SSL certificate path
- `SSL_KEY_PATH=/app/ssl/dashboard.key`: SSL key path
- `SECRET_KEY`: Flask session security

### Environment Variables (PO Processor)
- `FILEMAKER_ENABLED=true`: Enable FileMaker integration
- `FILEMAKER_SERVER=https://192.168.0.105:443`: FileMaker server URL
- `FILEMAKER_DATABASE=PreInventory`: Database name
- `FILEMAKER_USERNAME=JSON`: API username
- `FILEMAKER_PASSWORD=Windu63Purple!`: API password

## 🔄 Auto-Start & Self-Healing

### Cron Jobs
```cron
# Health check every 5 minutes with auto-recovery
*/5 * * * * /volume1/Main/Main/ParkerPOsOCR/po-system.sh health >/dev/null 2>&1

# Auto-start on boot
@reboot sleep 60 && /volume1/Main/Main/ParkerPOsOCR/po-system.sh start
```

### Docker Features
- `restart: unless-stopped`: Automatic container restart on failure
- `healthcheck`: Built-in health monitoring for dashboard
- `depends_on`: Ensures proper startup order

## 🌐 Access Points

- **Dashboard**: `https://192.168.0.62:8443` (HTTPS with self-signed cert)
- **Container Network**: Services communicate via `po-network`
- **Volume Mounts**: Shared access to Scans, POs, Archive, Errors folders

## 📊 Monitoring

### Health Status
```bash
# Check container status
docker-compose -f docker-compose-complete.yml ps

# View live logs
docker-compose -f docker-compose-complete.yml logs -f

# Check specific service
docker-compose -f docker-compose-complete.yml logs dashboard
```

### Log Locations
- **System Management**: `/volume1/Main/Main/ParkerPOsOCR/system-manager.log`
- **Dashboard Security**: `./dashboard/logs/security.log`
- **PO Processing**: `./docker_system/logs/`

## 🔐 Security Features

- **HTTPS**: Self-signed certificates for encrypted communication
- **Authentication**: Login required for dashboard access
- **Rate Limiting**: API endpoint protection
- **IP Logging**: Security event tracking
- **Container Isolation**: Isolated network environment

## 📁 File Structure
```
/volume1/Main/Main/ParkerPOsOCR/
├── docker-compose-complete.yml    # Main orchestration file
├── po-system.sh                   # Management script
├── Scans/                         # Input folder (monitored)
├── POs/                           # Processed output
├── Archive/                       # Completed files
├── Errors/                        # Failed processing
├── dashboard/
│   ├── Dockerfile.dashboard
│   ├── app_secure.py
│   └── ssl/
└── docker_system/
    ├── Dockerfile
    └── scripts/
```

## 🧹 Old System Cleanup

The following legacy components were replaced:
- ❌ Standalone dashboard service scripts
- ❌ Complex watchdog monitoring
- ❌ Multiple competing cron jobs
- ❌ Manual port conflict management
- ❌ Service script PID management

## ✅ Production Ready

This architecture is now production-ready with:
- Zero-downtime deployments via Docker Compose
- Automatic recovery from failures
- Centralized logging and monitoring
- Simplified maintenance and troubleshooting
- Scalable design for future enhancements

---

**Last Updated**: August 15, 2025  
**Status**: ✅ PRODUCTION READY

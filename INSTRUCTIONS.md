# Parker PO OCR System - Quick Start Instructions

## 🚀 Quick Commands

### Using the Restart Script (Recommended)
```bash
# Navigate to project directory
cd /volume1/Main/Main/ParkerPOsOCR

# Make script executable (one-time setup)
chmod +x restart_po_system.sh

# Start the system
./restart_po_system.sh start

# Check status
./restart_po_system.sh status

# View logs
./restart_po_system.sh logs

# Restart the system
./restart_po_system.sh restart

# Rebuild after code changes
./restart_po_system.sh rebuild

# Stop the system
./restart_po_system.sh stop
```

### Manual Docker Commands
```bash
# Navigate to docker directory
cd /volume1/Main/Main/ParkerPOsOCR/docker_system

# Start system
docker-compose up -d

# View logs
docker-compose logs -f

# Restart system
docker-compose restart

# Rebuild and start
docker-compose up --build -d

# Stop system
docker-compose down

# Check container status
docker ps
```

## 📁 File Processing

### To Process PDFs:
1. **Place PDF files** in: `/volume1/Main/Main/ParkerPOsOCR/Scans/`
2. **System automatically processes** them within 2 seconds
3. **Check results** in: `/volume1/Main/Main/ParkerPOsOCR/POs/`
4. **Failed files** go to: `/volume1/Main/Main/ParkerPOsOCR/Errors/`

### Monitoring Processing:
```bash
# Watch logs in real-time
./restart_po_system.sh logs

# Check processing log file
tail -f /volume1/Main/Main/ParkerPOsOCR/POs/po_processor.log

# List current files
ls -la /volume1/Main/Main/ParkerPOsOCR/Scans/
ls -la /volume1/Main/Main/ParkerPOsOCR/POs/
```

## 🔧 Troubleshooting

### Container Won't Start
```bash
# Check for errors
./restart_po_system.sh status
docker-compose logs

# Force rebuild
./restart_po_system.sh rebuild
```

### Files Not Processing
```bash
# Check if container is running
./restart_po_system.sh status

# Check logs for errors
./restart_po_system.sh logs

# Verify file permissions
ls -la /volume1/Main/Main/ParkerPOsOCR/Scans/
```

### High Memory Usage
```bash
# Check container resources
docker stats po-processor

# Restart to clear memory
./restart_po_system.sh restart
```

## 📊 System Health Checks

### Quick Health Check
```bash
# 1. Check container status
./restart_po_system.sh status

# 2. Test with a small PDF
# Place a test PDF in Scans folder and watch logs
./restart_po_system.sh logs

# 3. Verify folder structure
ls -la /volume1/Main/Main/ParkerPOsOCR/
```

### Performance Monitoring
```bash
# Monitor container resources
docker stats po-processor

# Check disk space
df -h /volume1/Main/Main/ParkerPOsOCR/

# View recent processing activity
tail -20 /volume1/Main/Main/ParkerPOsOCR/POs/po_processor.log
```

## 🆘 Emergency Commands

### Force Stop Everything
```bash
docker stop po-processor
docker rm po-processor
```

### Clean Reset
```bash
cd /volume1/Main/Main/ParkerPOsOCR/docker_system
docker-compose down
docker system prune -f
docker-compose up --build -d
```

### Backup Before Major Changes
```bash
# Backup current configuration
tar -czf po_system_backup_$(date +%Y%m%d).tar.gz /volume1/Main/Main/ParkerPOsOCR/docker_system/
```

---

## 📞 Support

**System Status:** ✅ Operational  
**Last Updated:** August 13, 2025  
**OCR Issues:** ✅ Resolved  

For issues, check:
1. Container logs: `./restart_po_system.sh logs`
2. Processing logs: `/volume1/Main/Main/ParkerPOsOCR/POs/po_processor.log`
3. Error files: `/volume1/Main/Main/ParkerPOsOCR/Errors/`

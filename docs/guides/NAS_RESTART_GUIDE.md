# 🔄 NAS Restart Recovery Guide

## 🚨 What Happens When NAS Restarts?

### ✅ **After Fix (Current Configuration)**
With `restart: unless-stopped` policy:

1. **NAS restarts** → **Docker daemon starts** → **Container automatically restarts**
2. **File monitoring resumes** within 30-60 seconds
3. **Processing continues** for any files in Scans folder
4. **No manual intervention** required

### ❌ **Before Fix (Previous Configuration)**
With `restart: 'no'` policy:
- Container would stay stopped after NAS restart
- Manual restart required: `./simple_restart.sh start`
- Files would accumulate unprocessed

## 🛡️ **Resilience Features**

### Docker Auto-Restart Policy
```yaml
restart: unless-stopped
```
**Behavior:**
- Restarts automatically after NAS reboot
- Restarts if container crashes
- Only stops if manually stopped with `docker stop`

### File System Monitoring
The `watchdog` library automatically:
- Resumes monitoring the Scans folder
- Processes any files that arrived during downtime
- Handles file system events robustly

### Data Persistence
All important data persists across restarts:
- **Input files**: Stored on NAS volume (`/Scans`)
- **Output files**: Stored on NAS volume (`/POs`, `/Archive`, `/Errors`)
- **Logs**: Stored on NAS volume (`/logs`)
- **Container config**: Stored in `docker-compose.yml`

## ⏱️ **Recovery Timeline**

| Time | Event |
|------|-------|
| T+0s | NAS shuts down |
| T+30-120s | NAS boots up |
| T+120-180s | Docker daemon starts |
| T+180-240s | Container auto-starts |
| T+240-300s | File monitoring active |

**Total downtime:** ~4-5 minutes typical

## 🔍 **How to Verify Recovery**

### 1. Check Container Status
```bash
cd /volume1/Main/Main/ParkerPOsOCR
./simple_restart.sh status
```

### 2. Verify File Monitoring
```bash
# Watch logs to see monitoring start
./simple_restart.sh logs

# Look for this message:
# "Folder monitoring active - waiting for PDF files..."
```

### 3. Test Processing
```bash
# Place a test file and watch processing
cp test.pdf /volume1/Main/Main/ParkerPOsOCR/Scans/
./simple_restart.sh logs
```

## 🚨 **Potential Issues and Solutions**

### Issue 1: Container Doesn't Auto-Start
**Symptoms:** No container running after NAS restart
```bash
./simple_restart.sh status  # Shows "Container not running"
```

**Solutions:**
```bash
# Check Docker daemon
docker info

# Manual start
./simple_restart.sh start

# Force rebuild if needed
./simple_restart.sh rebuild
```

### Issue 2: Files Not Processing After Restart
**Symptoms:** Files stay in Scans folder, no log activity

**Solutions:**
```bash
# Check logs for errors
./simple_restart.sh logs

# Restart container
./simple_restart.sh restart

# Check file permissions
ls -la /volume1/Main/Main/ParkerPOsOCR/Scans/
```

### Issue 3: Volume Mount Issues
**Symptoms:** Container starts but can't access files

**Solutions:**
```bash
# Check volume mounts
docker inspect po-processor | grep -A 10 "Mounts"

# Verify folder permissions
chmod 755 /volume1/Main/Main/ParkerPOsOCR/Scans/
chmod 755 /volume1/Main/Main/ParkerPOsOCR/POs/
```

## 📋 **Post-Restart Checklist**

### Automatic Checks (5 minutes after reboot)
- [ ] NAS web interface accessible
- [ ] SSH access working
- [ ] Docker daemon running: `docker info`

### Container Health Check
```bash
cd /volume1/Main/Main/ParkerPOsOCR

# 1. Verify container is running
./simple_restart.sh status

# 2. Check recent logs
./simple_restart.sh logs | tail -20

# 3. Verify file monitoring
# Look for "Folder monitoring active" message

# 4. Test with a file (optional)
# cp test.pdf Scans/ && watch logs
```

### If Issues Found
```bash
# Try automatic restart
./simple_restart.sh restart

# If that fails, rebuild
./simple_restart.sh rebuild

# Check for system issues
docker system df
docker system prune -f  # Clean up if needed
```

## 🔧 **Backup Recovery Plan**

### Emergency Manual Start
If auto-restart fails:
```bash
cd /volume1/Main/Main/ParkerPOsOCR/docker_system
docker-compose up -d
```

### Complete Rebuild
If container is corrupted:
```bash
cd /volume1/Main/Main/ParkerPOsOCR/docker_system
docker-compose down
docker system prune -f
docker-compose up --build -d
```

### Restore from Backup
If configuration is lost:
```bash
# Restore from backup (if available)
tar -xzf po_system_backup_YYYYMMDD.tar.gz

# Or re-download from source control
# git pull origin main  # If using git
```

## 📊 **Monitoring Best Practices**

### Set Up Monitoring
1. **Create a monitoring script:**
```bash
#!/bin/bash
# monitor_po_system.sh
while true; do
    if ! docker ps | grep -q po-processor; then
        echo "$(date): PO Processor DOWN - attempting restart"
        cd /volume1/Main/Main/ParkerPOsOCR
        ./simple_restart.sh start
    fi
    sleep 300  # Check every 5 minutes
done
```

2. **Add to cron for automatic monitoring:**
```bash
# Add to crontab
*/5 * * * * /volume1/Main/Main/ParkerPOsOCR/monitor_po_system.sh
```

### Health Check Notifications
Consider setting up:
- Email alerts when container stops
- Slack/Teams notifications for issues
- Log file size monitoring
- Processing queue alerts

## 🎯 **Best Practices**

1. **Regular Testing**: Test restart procedure monthly
2. **Backup Configuration**: Backup docker-compose.yml and scripts
3. **Monitor Logs**: Check logs weekly for issues
4. **Update Strategy**: Plan for system updates
5. **Documentation**: Keep recovery procedures updated

---

**Key Takeaway:** With the updated `restart: unless-stopped` policy, the system should automatically recover from NAS restarts with minimal downtime (4-5 minutes typical).

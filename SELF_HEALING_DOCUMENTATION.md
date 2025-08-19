# 🛡️ ParkerPOsOCR Self-Healing System Documentation

## 🎯 Overview

The ParkerPOsOCR system has been enhanced with comprehensive self-healing capabilities to ensure maximum uptime and automatic recovery from common failures. The system now monitors all critical components and automatically restarts failed services without manual intervention.

## 🔧 Self-Healing Components

### 1. **System Health Monitor** (`system_health_monitor.sh`)
**Location:** `/volume1/Main/Main/ParkerPOsOCR/system_health_monitor.sh`

**Monitors:**
- ✅ Docker daemon health
- ✅ PO processor container status
- ✅ Dashboard web service (HTTPS on port 9443)
- ⚠️ Mac PDF monitor (optional, non-critical)

**Features:**
- Comprehensive health checks with timeouts
- Automatic service recovery
- Configurable failure thresholds
- Detailed logging with timestamps
- Cron job integration for continuous monitoring
- Reboot recovery support

### 2. **Docker Container Health Checks**
**Location:** `docker_system/docker-compose.yml`

**Features:**
- Container restart policy: `unless-stopped`
- Built-in health checks for po-processor container
- Automatic container restart on failure
- Health monitoring every 30 seconds
- Graceful startup period (60 seconds)

### 3. **Enhanced Dashboard Startup** (`dashboard/start_dashboard.sh`)
**Location:** `/volume1/Main/Main/ParkerPOsOCR/dashboard/start_dashboard.sh`

**Features:**
- Auto-detection of HTTPS vs HTTP dashboard
- Process monitoring every 30 seconds
- Responsiveness checks (not just process existence)
- Consecutive failure threshold (3 failures trigger restart)
- Automatic cleanup of zombie processes
- Enhanced logging with timestamps

### 4. **Mac PDF Monitor Self-Healing** (`mac_monitor_selfheal.sh`)
**Location:** `/volume1/Main/Main/ParkerPOsOCR/mac_monitor_selfheal.sh`

**Features:**
- Remote SSH-based health monitoring
- LaunchAgent service monitoring
- Automatic service restart via SSH
- Local Mac self-healing script installation
- Cron-based monitoring (every 10 minutes)
- **Non-destructive enhancement** - does not modify existing functionality

## 🚀 Usage Guide

### Basic Health Check
```bash
# Single health check
./system_health_monitor.sh check

# Detailed system status
./system_health_monitor.sh status
```

### Continuous Monitoring
```bash
# Watch mode (interactive)
./system_health_monitor.sh watch

# Setup automatic monitoring (cron jobs)
./system_health_monitor.sh setup
```

### Manual Recovery
```bash
# Force system recovery
./system_health_monitor.sh recover

# Mac PDF monitor check
./mac_monitor_selfheal.sh check
```

### Mac Integration Setup
```bash
# Install Mac self-healing (run once)
./mac_monitor_selfheal.sh install-healing

# Check Mac system status
./mac_monitor_selfheal.sh status
```

## 📊 Monitoring Levels

### **Level 1: Automatic (Cron-based)**
- **Frequency:** Every 5 minutes
- **Action:** Silent auto-healing
- **Coverage:** Docker, PO Container, Dashboard
- **Setup:** `./system_health_monitor.sh setup`

### **Level 2: Boot Recovery**
- **Trigger:** System reboot
- **Action:** Automatic service startup after 2 minutes
- **Coverage:** All services
- **Setup:** Included in Level 1 setup

### **Level 3: Mac PDF Monitor**
- **Frequency:** Every 10 minutes (optional)
- **Action:** LaunchAgent restart
- **Coverage:** PDF printing functionality
- **Setup:** `./mac_monitor_selfheal.sh install-healing`

### **Level 4: Interactive Monitoring**
- **Frequency:** Every 2 minutes
- **Action:** Real-time alerts and recovery
- **Coverage:** All components + detailed logging
- **Usage:** `./system_health_monitor.sh watch`

## 🛡️ Failure Recovery Scenarios

### **Scenario 1: PO Container Crash**
1. Health monitor detects container is down
2. Executes `docker-compose restart po-processor`
3. Waits 10 seconds for startup
4. Verifies container is running
5. Logs success/failure

### **Scenario 2: Dashboard Unresponsive**
1. Health monitor detects port open but no HTTP response
2. Terminates existing dashboard processes
3. Restarts dashboard service
4. Verifies HTTPS response on port 9443
5. Logs recovery status

### **Scenario 3: Mac PDF Monitor Stopped**
1. Mac self-healing script detects missing process
2. Kills any zombie processes
3. Restarts LaunchAgent service
4. Verifies process is running
5. Logs to Mac-local log file

### **Scenario 4: NAS System Reboot**
1. Docker containers auto-start (unless-stopped policy)
2. Cron jobs automatically resume monitoring after 2 minutes
3. All services automatically validated and recovered if needed
4. Mac PDF monitor auto-starts via LaunchAgent

## 📁 Log Files

### **System Health Monitor**
- **File:** `/volume1/Main/Main/ParkerPOsOCR/system_health.log`
- **Content:** All health checks, recoveries, and system events
- **Rotation:** Manual (recommend weekly review)

### **Dashboard Startup**
- **File:** `/volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log`
- **Content:** Dashboard startup, restart, and health events
- **Rotation:** Automatic via nohup

### **Mac PDF Monitor**
- **File:** `/Users/Shared/ParkerPOsOCR/self_healing.log` (on Mac)
- **Content:** Mac-specific health checks and LaunchAgent restarts
- **Rotation:** Manual

## 🔍 Status Verification

### **Check Overall System Health**
```bash
./system_health_monitor.sh status
```
**Expected Output:**
```
📊 ParkerPOsOCR System Status Report
====================================
✅ Docker daemon: HEALTHY
✅ PO container: RUNNING  
✅ Dashboard: HEALTHY
⚠️ Mac PDF monitor: NOT RESPONDING (this is optional)
🎯 OVERALL SYSTEM STATUS: HEALTHY
```

### **Check Cron Jobs**
```bash
crontab -l | grep system_health_monitor
```
**Expected Output:**
```
*/5 * * * * /volume1/Main/Main/ParkerPOsOCR/system_health_monitor.sh auto-heal >/dev/null 2>&1
@reboot sleep 120 && /volume1/Main/Main/ParkerPOsOCR/system_health_monitor.sh auto-heal >/dev/null 2>&1
```

### **Check Docker Container Health**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.State}}"
```

### **Check Mac PDF Monitor (from NAS)**
```bash
./mac_monitor_selfheal.sh status
```

## ⚠️ Important Notes

### **Preserving Existing Functionality**
- ✅ **Mac folder watch to print function remains intact**
- ✅ **No changes to existing LaunchAgent configuration**
- ✅ **All existing PO processing workflows preserved**
- ✅ **Dashboard notification system unchanged**

### **Non-Breaking Enhancements**
- Self-healing scripts **add monitoring only**
- Existing configurations are **not modified**
- Mac PDF monitor enhancements are **completely optional**
- System can function normally **without self-healing enabled**

### **Recovery Limitations**
- **Docker daemon failures** require manual intervention
- **Network connectivity issues** may prevent Mac monitoring
- **Hardware failures** cannot be automatically resolved
- **File system corruption** requires manual recovery

## 🎯 Recommended Setup

### **For Production Use:**
1. **Enable automatic monitoring:**
   ```bash
   ./system_health_monitor.sh setup
   ```

2. **Install Mac self-healing (optional):**
   ```bash
   ./mac_monitor_selfheal.sh install-healing
   ```

3. **Verify setup:**
   ```bash
   ./system_health_monitor.sh status
   crontab -l
   ```

### **For Development/Testing:**
1. **Use interactive monitoring:**
   ```bash
   ./system_health_monitor.sh watch
   ```

2. **Manual health checks as needed:**
   ```bash
   ./system_health_monitor.sh check
   ```

## 🚨 Emergency Procedures

### **If Self-Healing Fails:**
1. **Manual container restart:**
   ```bash
   cd /volume1/Main/Main/ParkerPOsOCR/docker_system
   docker-compose restart
   ```

2. **Manual dashboard restart:**
   ```bash
   cd /volume1/Main/Main/ParkerPOsOCR/dashboard
   pkill -f "python.*app"
   nohup sh start_dashboard.sh &
   ```

3. **Disable auto-monitoring (if needed):**
   ```bash
   crontab -l | grep -v system_health_monitor | crontab -
   ```

### **Complete System Reset:**
```bash
# Stop all services
docker-compose -f /volume1/Main/Main/ParkerPOsOCR/docker_system/docker-compose.yml down
pkill -f dashboard

# Clean Docker system
docker system prune -f

# Restart everything
cd /volume1/Main/Main/ParkerPOsOCR/docker_system
docker-compose up -d

cd /volume1/Main/Main/ParkerPOsOCR/dashboard  
nohup sh start_dashboard.sh &
```

---

## ✅ Summary

The ParkerPOsOCR system now features **comprehensive self-healing capabilities** that:

1. **Monitor all critical components** continuously
2. **Automatically recover** from common failure scenarios  
3. **Preserve existing functionality** without modification
4. **Provide detailed logging** for troubleshooting
5. **Scale from basic to advanced monitoring** based on needs

The system is now **production-ready** with enterprise-level reliability and minimal manual intervention requirements.

**🎉 Result: Maximum uptime with zero operational overhead!**

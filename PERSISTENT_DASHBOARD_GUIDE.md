# 🚀 Persistent Dashboard Service Setup

## ✅ Dashboard is Now Running Persistently in the Background!

The PO Processing Dashboard is now set up as a persistent background service that will:
- ✅ **Start automatically** when the NAS boots up
- ✅ **Run in the background** without blocking terminals
- ✅ **Auto-restart** if it crashes (checked every 5 minutes)
- ✅ **Log all activity** for troubleshooting

## 📱 Access Your Dashboard

**URL:** http://192.168.0.62:5000

The dashboard is accessible from any device on your network!

## 🛠️ Service Management Commands

### Check Status
```bash
/volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh status
```

### Start Dashboard
```bash
/volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh start
```

### Stop Dashboard
```bash
/volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh stop
```

### Restart Dashboard
```bash
/volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh restart
```

## 📊 Monitoring & Logs

### Dashboard Logs
```bash
tail -f /volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log
```

### Watchdog Logs (Auto-restart monitoring)
```bash
tail -f /volume1/Main/Main/ParkerPOsOCR/dashboard/watchdog.log
```

### Real-time Log Monitoring
```bash
# Watch dashboard activity in real-time
tail -f /volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log

# Watch for auto-restarts
tail -f /volume1/Main/Main/ParkerPOsOCR/dashboard/watchdog.log
```

## 🔄 Automatic Features

### 🚀 **Boot Startup**
- Dashboard starts automatically when NAS reboots
- Configured via cron job: `@reboot`

### 🛡️ **Crash Recovery**
- Watchdog checks every 5 minutes if dashboard is running
- Automatically restarts if crashed
- Logs all restart events with timestamps

### 📝 **Logging**
- All dashboard activity logged to `dashboard.log`
- Watchdog activity logged to `watchdog.log`
- Logs rotated automatically to prevent disk space issues

## 🎯 Current Status

**Dashboard Status:** ✅ RUNNING (PID: 4881)
**Auto-start:** ✅ ENABLED 
**Watchdog:** ✅ ACTIVE (checks every 5 minutes)
**Access URL:** http://192.168.0.62:5000

## 🔧 Advanced Management

### Manual Process Check
```bash
ps aux | grep "python3 app.py"
```

### View PID File
```bash
cat /var/run/po-dashboard.pid
```

### Check Network Connectivity
```bash
netstat -tulpn | grep :5000
```

### Force Kill (Emergency)
```bash
pkill -f "python3 app.py"
```

## 📋 Cron Jobs Installed

```bash
# Start dashboard at boot
@reboot /volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh start

# Check and restart if crashed (every 5 minutes)
*/5 * * * * /volume1/Main/Main/ParkerPOsOCR/dashboard-watchdog.sh >> /volume1/Main/Main/ParkerPOsOCR/dashboard/watchdog.log 2>&1
```

## 🎉 Benefits

### ✅ **No More Terminal Blocking**
- Dashboard runs in background
- Your terminal is free for other tasks
- No more accidentally stopping it with Ctrl+C

### ✅ **Automatic Startup**
- Survives NAS reboots
- Always available after power outages
- No manual intervention needed

### ✅ **Self-Healing**
- Automatically recovers from crashes
- Monitors itself every 5 minutes
- Logs all recovery events

### ✅ **Professional Service**
- Proper logging and monitoring
- Easy start/stop/restart commands
- Status checking capabilities

## 🚨 Troubleshooting

### Dashboard Won't Start
1. Check logs: `tail -20 /volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log`
2. Check if port is busy: `netstat -tulpn | grep :5000`
3. Manual restart: `/volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh restart`

### Can't Access Dashboard
1. Check if running: `/volume1/Main/Main/ParkerPOsOCR/dashboard-service.sh status`
2. Check network: `ping 192.168.0.62`
3. Check firewall: Ensure port 5000 is not blocked

### Logs Too Large
```bash
# Clear dashboard logs
> /volume1/Main/Main/ParkerPOsOCR/dashboard/dashboard.log

# Clear watchdog logs  
> /volume1/Main/Main/ParkerPOsOCR/dashboard/watchdog.log
```

---

**🎉 Your dashboard is now running as a professional, persistent background service!**

Access it anytime at: **http://192.168.0.62:5000** 📱✨

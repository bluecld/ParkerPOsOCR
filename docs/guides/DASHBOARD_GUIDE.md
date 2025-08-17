# 🖥️ Web Dashboard - Complete Monitoring Solution

## 🎯 **Dashboard Overview**

**URL:** http://192.168.0.62:5000 (or your NAS IP)  
**Status:** ✅ **RUNNING**  
**Auto-refresh:** Every 30 seconds  

### 📊 **Dashboard Features**

#### 1. **Real-Time Container Monitoring**
- Container status (Running/Stopped)
- CPU and Memory usage
- Restart policy verification
- Container uptime tracking

#### 2. **Processing Statistics**
- Files in queue (waiting to be processed)
- Completed PO count
- Error count tracking
- Total processing metrics

#### 3. **Performance Metrics**
- Real-time CPU usage graphs
- Memory consumption monitoring
- Disk space utilization
- System uptime display

#### 4. **Recent Activity Log**
- Live processing activity feed
- Error and warning notifications
- Timestamp tracking
- Auto-scrolling log viewer

#### 5. **Completed Files Management**
- List of processed PO folders
- Direct download links to JSON data
- PDF file count per PO
- Processing timestamp tracking

#### 6. **System Health Monitoring**
- Container health status
- File processing status
- Restart policy verification
- System uptime tracking

#### 7. **FileMaker Integration Prep**
- Export data for FileMaker ERP
- JSON format compatible with FileMaker Data API
- Batch export functionality
- Processing statistics included

## 🚀 **Quick Start**

### Start Dashboard
```bash
cd /volume1/Main/Main/ParkerPOsOCR/dashboard
./start_dashboard.sh
```

### Access Dashboard
```
URL: http://[YOUR_NAS_IP]:5000
Default Port: 5000
Auto-refresh: 30 seconds
```

## 📱 **Dashboard Sections**

### 1. **Top Status Cards**
- **Container Status**: Running/Stopped with uptime
- **Files in Queue**: PDFs waiting for processing  
- **Completed POs**: Successfully processed files
- **Errors**: Failed processing attempts

### 2. **Performance Panel**
- **CPU Usage**: Real-time container CPU consumption
- **Memory Usage**: RAM usage with percentage and MB
- **Disk Usage**: Storage space utilization

### 3. **Activity Feed**
- **Live Logs**: Real-time processing activity
- **Color Coded**: Info (Blue), Warnings (Yellow), Errors (Red)
- **Auto-scroll**: Latest activity always visible

### 4. **Completed Files Table**
- **PO Number**: Processed purchase order numbers
- **Completion Time**: When processing finished
- **JSON Links**: Direct download of extracted data
- **PDF Count**: Number of PDF files per PO
- **Actions**: View details button

### 5. **System Health Panel**
- **Container Health**: Good/Warning/Critical status
- **Processing Status**: Active/Inactive
- **Restart Policy**: Auto-restart configuration
- **System Uptime**: How long system has been running

### 6. **Control Buttons**
- **Restart Container**: Emergency restart capability
- **View Full Logs**: Complete log file viewer
- **Export to FileMaker**: Generate ERP-ready data

## 🔗 **FileMaker ERP Integration**

### Export Features
The dashboard includes specialized FileMaker export functionality:

#### **Export Data Structure**
```json
{
  "timestamp": "2025-08-13T14:30:00",
  "completed_pos": [
    {
      "po_number": "455XXXXX",
      "created": "2025-08-13 14:25:00",
      "extracted_data": {
        "po_info": {...},
        "line_items": [...],
        "vendor_details": {...}
      },
      "files": {
        "json_files": [...],
        "pdf_files": [...]
      }
    }
  ],
  "stats": {
    "total_processed": 25,
    "success_rate": 95.2,
    "error_count": 2
  }
}
```

#### **FileMaker Field Mapping**
- **PO_Number**: Purchase order number
- **Processing_Date**: When OCR completed
- **JSON_Data**: Complete extracted data
- **PDF_Count**: Number of PDF files
- **Status**: Processing status
- **Source_System**: "Parker_PO_OCR"

### Integration Steps
1. **Configure FileMaker Server**: Update `filemaker_config.json`
2. **Set Database Layout**: Specify target layout name
3. **Map Fields**: Adjust field mapping to match your schema
4. **Test Connection**: Verify FileMaker Data API access
5. **Enable Auto-Sync**: Set up automatic data transfer

## 📊 **API Endpoints**

The dashboard provides REST API endpoints for integration:

### **Available Endpoints**
```bash
GET /api/status          # Container status
GET /api/stats           # Processing statistics  
GET /api/activity        # Recent activity log
GET /api/completed       # Completed files list
GET /api/health          # System health metrics
GET /api/logs            # Full system logs
GET /api/json/<file>     # Download JSON files
POST /api/restart        # Restart container
```

### **Example API Usage**
```bash
# Get container status
curl http://192.168.0.62:5000/api/status

# Get processing stats
curl http://192.168.0.62:5000/api/stats

# Download specific JSON file
curl http://192.168.0.62:5000/api/json/455XXXXX/po_data.json
```

## 🔧 **Configuration**

### **Dashboard Settings**
```python
# In app.py
BASE_PATH = "/volume1/Main/Main/ParkerPOsOCR"
CONTAINER_NAME = "po-processor"
REFRESH_INTERVAL = 30  # seconds
```

### **FileMaker Configuration**
```json
{
  "filemaker": {
    "server_url": "https://your-filemaker-server.com",
    "database": "PO_Management",
    "username": "api_user", 
    "password": "secure_password",
    "layout_name": "PO_Processing"
  }
}
```

## 🛡️ **Security Notes**

### **Access Control**
- Dashboard runs on internal network only
- No authentication required (internal use)
- API endpoints accessible to local network
- File downloads restricted to PO directory

### **For Production Use**
Consider adding:
- Basic authentication
- HTTPS encryption
- Rate limiting
- Access logging

## 🔍 **Monitoring Best Practices**

### **Daily Checks**
1. **Container Status**: Verify running state
2. **Queue Length**: Check for file backlog
3. **Error Count**: Review failed processing
4. **Disk Space**: Monitor storage usage

### **Weekly Reviews**
1. **Processing Trends**: Analyze throughput
2. **Error Patterns**: Identify common issues
3. **Performance**: Check resource usage
4. **FileMaker Sync**: Verify data transfer

## 🆘 **Troubleshooting**

### **Dashboard Won't Start**
```bash
# Check Python installation
python3 --version

# Verify packages
pip3 list | grep -E "(flask|docker|psutil)"

# Check port availability
netstat -tulpn | grep :5000
```

### **No Container Data**
```bash
# Verify Docker socket
docker ps

# Check container name
docker ps | grep po-processor

# Test Docker Python connection
python3 -c "import docker; print(docker.from_env().containers.list())"
```

### **API Errors**
```bash
# Check dashboard logs
tail -f /var/log/dashboard.log

# Test API endpoints
curl http://localhost:5000/api/status

# Verify file permissions
ls -la /volume1/Main/Main/ParkerPOsOCR/POs/
```

---

## 🎯 **Key Benefits**

✅ **Real-time monitoring** of PO processing pipeline  
✅ **Complete visibility** into system health and performance  
✅ **Direct access** to processed data and JSON files  
✅ **FileMaker ERP integration** ready for your local server  
✅ **Responsive web interface** accessible from any device  
✅ **API endpoints** for custom integrations  
✅ **Automated data export** for business systems  

**The dashboard provides complete visibility and control over your PO processing system, with built-in FileMaker integration preparation for seamless ERP connectivity!** 🚀

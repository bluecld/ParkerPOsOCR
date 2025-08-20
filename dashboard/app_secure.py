# Secure Dashboard Web Server with Authentication
from flask import Flask, render_template, jsonify, send_file, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import docker
import json
import os
import glob
from datetime import datetime, timedelta
import subprocess
import psutil
import time
from pathlib import Path
import bcrypt
from dotenv import load_dotenv
import logging
from notifications import notification_manager
from functools import wraps
import ipaddress

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key-immediately')

# Configure Flask for better development experience
app.config['TEMPLATES_AUTO_RELOAD'] = os.getenv('TEMPLATES_AUTO_RELOAD', '1') == '1'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', '0') == '1'

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'
login_manager.login_message_category = 'info'

# Configure rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[
        f"{os.getenv('RATE_LIMIT_PER_MINUTE', 30)} per minute",
        f"{os.getenv('RATE_LIMIT_PER_HOUR', 200)} per hour"
    ]
)

# Configuration - Updated for containerized environment
BASE_PATH = "/app"
SCANS_PATH = f"{BASE_PATH}/Scans"
POS_PATH = f"{BASE_PATH}/POs"
ARCHIVE_PATH = f"{BASE_PATH}/Archive"
ERRORS_PATH = f"{BASE_PATH}/Errors"
LOG_PATH = f"{BASE_PATH}/POs/po_processor.log"
CONTAINER_NAME = "po-processor"

# Security configuration
ALLOWED_IPS = [ip.strip() for ip in os.getenv('ALLOWED_IPS', '').split(',') if ip.strip()]
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = bcrypt.hashpw(os.getenv('ADMIN_PASSWORD', 'admin').encode('utf-8'), bcrypt.gensalt())

# Setup logging for security events
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('/app/logs/security.log')
security_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
security_handler.setFormatter(security_formatter)
security_handler.setLevel(logging.DEBUG)  # Set handler level to DEBUG
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.DEBUG)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None

def ip_whitelist_required(f):
    """Decorator to check IP whitelist"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ALLOWED_IPS:
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            allowed = False
            for allowed_ip in ALLOWED_IPS:
                try:
                    if ipaddress.ip_address(client_ip) in ipaddress.ip_network(allowed_ip, strict=False):
                        allowed = True
                        break
                except:
                    if client_ip == allowed_ip:
                        allowed = True
                        break
            
            if not allowed:
                security_logger.warning(f"IP {client_ip} blocked - not in whitelist")
                return jsonify({'error': 'Access denied'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def add_security_headers(response):
    """Add security headers to response"""
    if os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true':
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; font-src 'self' cdnjs.cloudflare.com; img-src 'self' data:;"
    return response

app.after_request(add_security_headers)

# [Previous helper functions remain the same]
def get_docker_client():
    """Get Docker client"""
    try:
        return docker.from_env()
    except Exception as e:
        print(f"Docker connection error: {e}")
        return None

def get_container_status():
    """Get container status and stats"""
    client = get_docker_client()
    if not client:
        return {"status": "error", "message": "Docker not available"}
    
    try:
        container = client.containers.get(CONTAINER_NAME)
        stats = container.stats(stream=False)
        
        # Calculate CPU percentage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0
        
        # Calculate memory usage
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        memory_percent = (memory_usage / memory_limit) * 100.0
        
        return {
            "status": container.status,
            "id": container.short_id,
            "image": str(container.image.tags[0]) if container.image.tags else "unknown",
            "started_at": container.attrs['State']['StartedAt'],
            "restart_policy": container.attrs['HostConfig']['RestartPolicy']['Name'],
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_processing_stats():
    """Get file processing statistics"""
    stats = {
        "files_in_queue": 0,
        "completed_pos": 0,
        "error_files": 0
    }
    
    # Count files in Scans (queue)
    if os.path.exists(SCANS_PATH):
        scans = glob.glob(os.path.join(SCANS_PATH, "*.pdf"))
        stats["files_in_queue"] = len(scans)
    
    # Count completed POs
    if os.path.exists(POS_PATH):
        pos = [d for d in os.listdir(POS_PATH) if os.path.isdir(os.path.join(POS_PATH, d)) and d.startswith('455')]
        stats["completed_pos"] = len(pos)
    
    # Count error files
    if os.path.exists(ERRORS_PATH):
        errors = glob.glob(os.path.join(ERRORS_PATH, "*.pdf"))
        stats["error_files"] = len(errors)
    
    return stats

# [Continue with rest of helper functions...]

def get_recent_activity():
    """Get recent processing activity from logs"""
    activities = []
    
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()[-20:]  # Last 20 lines
            
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    # Parse log format: 2025-08-19 15:47:11,509 - INFO - message
                    parts = line.strip().split(' - ', 2)
                    if len(parts) >= 3:
                        timestamp = parts[0]
                        level = parts[1]
                        message = parts[2]
                        
                        activities.append({
                            "timestamp": timestamp,
                            "level": level,
                            "message": message
                        })
                    else:
                        # Fallback for other formats
                        activities.append({
                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "level": "INFO",
                            "message": line.strip()
                        })
        except Exception as e:
            activities.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "level": "ERROR",
                "message": f"Error reading log file: {str(e)}"
            })
    
    return activities

def get_completed_files():
    """Get list of completed PO files with JSON data"""
    completed = []
    
    if os.path.exists(POS_PATH):
        po_folders = [d for d in os.listdir(POS_PATH) if os.path.isdir(os.path.join(POS_PATH, d)) and d.startswith('455')]
        
        # Sort by creation time (most recent first)
        po_folders_with_time = []
        for folder in po_folders:
            folder_path = os.path.join(POS_PATH, folder)
            creation_time = os.path.getctime(folder_path)
            po_folders_with_time.append((folder, creation_time))
        
        # Sort by creation time descending (newest first)
        po_folders_sorted = [folder for folder, _ in sorted(po_folders_with_time, key=lambda x: x[1], reverse=True)]
        
        for folder in po_folders_sorted[:50]:  # Last 50 completed files (increased from 10)
            folder_path = os.path.join(POS_PATH, folder)
            json_files = glob.glob(os.path.join(folder_path, "*.json"))
            
            folder_info = {
                "po_number": folder,
                "created": datetime.fromtimestamp(os.path.getctime(folder_path)).strftime('%Y-%m-%d %H:%M:%S'),
                "json_files": [],
                "pdf_files": []
            }
            
            # Get JSON files
            for json_file in json_files:
                filename = os.path.basename(json_file)
                folder_info["json_files"].append({
                    "name": filename,
                    "path": json_file,
                    "size": os.path.getsize(json_file)
                })
            
            # Get PDF files
            pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
            for pdf_file in pdf_files:
                filename = os.path.basename(pdf_file)
                folder_info["pdf_files"].append({
                    "name": filename,
                    "path": pdf_file,
                    "size": os.path.getsize(pdf_file)
                })
            
            completed.append(folder_info)
    
    return completed

def get_system_health():
    """Get overall system health metrics"""
    health = {
        "timestamp": datetime.now().isoformat(),
        "container": get_container_status(),
        "processing": get_processing_stats(),
        "disk_usage": {},
        "uptime": "",
        "docker_version": ""
    }
    
    # Get disk usage
    try:
        disk_usage = psutil.disk_usage('/')
        health["disk_usage"] = {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "percent": round((disk_usage.used / disk_usage.total) * 100, 2)
        }
    except:
        health["disk_usage"] = {"error": "Unable to get disk usage"}
    
    # Get system uptime
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = uptime_seconds / 3600
        if uptime_hours < 24:
            health["uptime"] = f"{uptime_hours:.1f} hours"
        else:
            uptime_days = uptime_hours / 24
            health["uptime"] = f"{uptime_days:.1f} days"
    except:
        health["uptime"] = "Unknown"
    
    return health

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
@ip_whitelist_required
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH):
            user = User(username)
            login_user(user, remember=True, duration=timedelta(minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))))
            security_logger.info(f"Successful login from {request.remote_addr} for user {username}")
            return redirect(url_for('dashboard'))
        else:
            security_logger.warning(f"Failed login attempt from {request.remote_addr} for user {username}")
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    security_logger.info(f"User {current_user.id} logged out from {request.remote_addr}")
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Main Routes
@app.route('/')
@login_required
@ip_whitelist_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/test')
def test():
    try:
        return "<h1>Secure Dashboard Test - HTTPS Working!</h1><p>If you see this, HTTPS is working correctly.</p><a href='/login'>Go to Login</a>"
    except Exception as e:
        print(f"Error in test route: {e}")
        return f"Error: {e}", 500

# API Routes (all require authentication)
@app.route('/api/status')
@login_required
@ip_whitelist_required
def api_status():
    """API endpoint for container status"""
    return jsonify(get_container_status())

@app.route('/api/stats')
@login_required
@ip_whitelist_required
def api_stats():
    """API endpoint for processing statistics"""
    return jsonify(get_processing_stats())

@app.route('/api/activity')
@login_required
@ip_whitelist_required
def api_activity():
    """API endpoint for recent activity"""
    return jsonify(get_recent_activity())

@app.route('/api/completed')
@login_required
@ip_whitelist_required
def api_completed():
    """API endpoint for completed files"""
    return jsonify(get_completed_files())

@app.route('/api/health')
@login_required
@ip_whitelist_required
def api_health():
    """API endpoint for system health"""
    return jsonify(get_system_health())

@app.route('/api/logs')
@login_required
@ip_whitelist_required
def api_logs():
    """API endpoint for full logs"""
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                logs = f.read()
            return {"logs": logs.split('\n')[-100:]}  # Last 100 lines
        else:
            return {"logs": ["No log file found"]}
    except Exception as e:
        return {"error": str(e)}

@app.route('/api/notification-settings', methods=['GET'])
@login_required
@ip_whitelist_required
def api_get_notification_settings():
    """API endpoint to get notification settings"""
    try:
        return jsonify(notification_manager.config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/notification-settings', methods=['POST'])
@login_required
@ip_whitelist_required
def api_save_notification_settings():
    """API endpoint to save notification settings"""
    try:
        config = request.json
        
        # Validate the configuration structure
        required_keys = ['email', 'pushover', 'telegram', 'webhook']
        if not all(key in config for key in required_keys):
            return jsonify({"status": "error", "message": "Invalid configuration structure"}), 400
        
        # Update the configuration
        notification_manager.config = config
        notification_manager.save_config()
        
        return jsonify({"status": "success", "message": "Notification settings saved successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/test-notifications', methods=['POST'])
@login_required
@ip_whitelist_required
def api_test_notifications():
    """API endpoint to test notifications"""
    try:
        data = request.json
        title = data.get('title', 'Test Notification')
        message = data.get('message', 'This is a test notification')
        
        # Send test notification
        results = notification_manager.send_notification(title, message, notification_type="info")
        
        return jsonify({
            "status": "success", 
            "results": results,
            "message": "Test notifications sent"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/json/<path:filename>')
@login_required
@ip_whitelist_required
def download_json(filename):
    """Download JSON file"""
    try:
        # Security: ensure file is within POs directory
        file_path = os.path.join(POS_PATH, filename)
        if not file_path.startswith(POS_PATH):
            return {"error": "Invalid file path"}, 403
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return {"error": "File not found"}, 404
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/po/<po_number>')
@login_required
@ip_whitelist_required
def api_po_details(po_number):
    """API endpoint for PO details"""
    try:
        # Find all files related to this PO
        po_folder = os.path.join(POS_PATH, po_number)
        
        if not os.path.exists(po_folder):
            return {"error": f"PO {po_number} not found"}, 404
        
        # Get all files in the PO folder
        json_files = []
        pdf_files = []
        text_files = []
        
        for file in os.listdir(po_folder):
            file_path = os.path.join(po_folder, file)
            if file.endswith('.json'):
                # Load JSON content
                try:
                    with open(file_path, 'r') as f:
                        json_content = json.load(f)
                    json_files.append({
                        "name": file,
                        "content": json_content,
                        "size": os.path.getsize(file_path)
                    })
                except:
                    json_files.append({
                        "name": file,
                        "content": "Error reading file",
                        "size": os.path.getsize(file_path)
                    })
            elif file.endswith('.pdf'):
                pdf_files.append({
                    "name": file,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
            elif file.endswith('.txt'):
                text_files.append({
                    "name": file,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
        
        # Get folder creation time
        folder_created = datetime.fromtimestamp(os.path.getctime(po_folder)).isoformat()
        
        po_details = {
            "po_number": po_number,
            "created": folder_created,
            "folder_path": po_folder,
            "json_files": json_files,
            "pdf_files": pdf_files,
            "text_files": text_files,
            "total_files": len(json_files) + len(pdf_files) + len(text_files)
        }
        
        # If there's a main JSON file, include its content at the top level
        main_json = next((j for j in json_files if j["name"] == f"{po_number}.json"), None)
        if main_json and isinstance(main_json["content"], dict):
            po_details.update(main_json["content"])
        
        return po_details
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/po/<po_number>/download')
@login_required
@ip_whitelist_required
def api_po_download(po_number):
    """Download complete PO data as JSON"""
    try:
        po_details = api_po_details(po_number)
        if isinstance(po_details, tuple):  # Error response
            return po_details
        
        # Create a downloadable JSON file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(po_details, f, indent=2, default=str)
            temp_path = f.name
        
        return send_file(temp_path, as_attachment=True, 
                        download_name=f"PO_{po_number}_details.json",
                        mimetype='application/json')
                        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/po/<po_number>/file/<filename>')
@login_required
@ip_whitelist_required
def api_po_file(po_number, filename):
    """View or download a specific file from a PO"""
    try:
        # Security: ensure file is within PO directory
        po_folder = os.path.join(POS_PATH, po_number)
        file_path = os.path.join(po_folder, filename)
        
        if not file_path.startswith(po_folder):
            return {"error": "Invalid file path"}, 403
        
        if not os.path.exists(file_path):
            return {"error": "File not found"}, 404
        
        # Determine if we should display inline or as attachment
        if filename.endswith('.txt'):
            # Display text files inline
            return send_file(file_path, mimetype='text/plain')
        elif filename.endswith('.json'):
            # Display JSON files inline
            return send_file(file_path, mimetype='application/json')
        elif filename.endswith('.pdf'):
            # Display PDF files inline in browser
            return send_file(file_path, mimetype='application/pdf')
        else:
            # Download other files
            return send_file(file_path, as_attachment=True)
            
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/notifications/send', methods=['POST'])
def api_send_notification():
    """API endpoint to receive notifications from processing containers"""
    # IMMEDIATE debug write to confirm function execution
    try:
        with open('/app/logs/function_debug.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - FUNCTION ENTRY: api_send_notification called\n")
            f.flush()
    except:
        pass
    
    try:
        data = request.get_json()
        if not data:
            return {"status": "error", "message": "No JSON data received"}, 400
        
        # Log the notification
        title = data.get('title', 'Notification')
        message = data.get('message', 'No message')
        po_number = data.get('po_number', 'Unknown')
        notification_type = data.get('type', 'info')
        
        # Log to security logger
        security_logger.info(f"Notification received: {title} - {message} (PO: {po_number}, Type: {notification_type})")
        
        # IMMEDIATE debug after logging
        try:
            with open('/app/logs/function_debug.log', 'a') as f:
                f.write(f"{datetime.now().isoformat()} - AFTER SECURITY LOG: {title}\n")
                f.flush()
        except:
            pass
        
        # Also write to the processor log file so Recent Activity can display it
        import sys
        print(f"[DEBUG PRINT] Starting log file write process", flush=True)
        sys.stdout.flush()
        print(f"[DEBUG PRINT] LOG_PATH: {LOG_PATH}", flush=True)
        sys.stdout.flush()
        try:
            # Write debug info to separate file to track execution
            with open('/app/logs/notification_debug.log', 'a') as debug_file:
                debug_file.write(f"{datetime.now().isoformat()} - NOTIFICATION DEBUG: Starting write process for {title}\n")
                debug_file.flush()
            
            log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]} - INFO - {title}: {message}"
            print(f"[DEBUG PRINT] Created log entry: {log_entry}", flush=True)
            sys.stdout.flush()
            security_logger.debug(f"Attempting to write to LOG_PATH: {LOG_PATH}")
            security_logger.debug(f"Log entry: {log_entry}")
            print(f"[DEBUG PRINT] Opening log file for writing", flush=True)
            sys.stdout.flush()
            
            # Debug file write before main operation
            with open('/app/logs/notification_debug.log', 'a') as debug_file:
                debug_file.write(f"{datetime.now().isoformat()} - About to write to processor log: {log_entry}\n")
                debug_file.flush()
            
            with open(LOG_PATH, 'a') as log_file:
                log_file.write(log_entry + '\n')
                log_file.flush()  # Force flush to ensure write
            print(f"[DEBUG PRINT] Successfully wrote to log file", flush=True)
            sys.stdout.flush()
            security_logger.debug(f"Successfully wrote notification to processor log")
            
            # Debug file write after successful operation
            with open('/app/logs/notification_debug.log', 'a') as debug_file:
                debug_file.write(f"{datetime.now().isoformat()} - SUCCESS: Wrote to processor log\n")
                debug_file.flush()
                
        except Exception as log_err:
            # Write exception to debug file
            with open('/app/logs/notification_debug.log', 'a') as debug_file:
                debug_file.write(f"{datetime.now().isoformat()} - ERROR: {str(log_err)}\n")
                debug_file.flush()
            print(f"[DEBUG PRINT] ERROR writing to log file: {log_err}", flush=True)
            sys.stdout.flush()
            security_logger.error(f"Failed to write notification to log file: {log_err}")
        
        # Dispatch via notification manager
        try:
            notification_manager.send_notification(title, message, po_number, notification_type)
        except Exception as notify_err:
            security_logger.error(f"Notification dispatch error: {notify_err}")

        # Store notification (you can extend this to store in database if needed)
        notification_data = {
            "title": title,
            "message": message,
            "po_number": po_number,
            "type": notification_type,
            "timestamp": datetime.now().isoformat()
        }
        
        return {"status": "success", "message": "Notification received", "data": notification_data}
    except Exception as e:
        security_logger.error(f"Failed to process notification: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/api/notifications/config', methods=['GET'])
@login_required
@ip_whitelist_required
def api_get_notification_config():
    """API endpoint to get notification configuration"""
    try:
        config_path = '/app/logs/notification_config.json'
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Remove sensitive data for client
            safe_config = config.copy()
            if 'email' in safe_config and 'password' in safe_config['email']:
                safe_config['email']['password'] = '••••••••'  # Mask password
            if 'pushover' in safe_config and 'api_token' in safe_config['pushover']:
                safe_config['pushover']['api_token'] = safe_config['pushover']['api_token'][:4] + '••••••••••••'  # Partially mask token
                safe_config['pushover']['user_key'] = safe_config['pushover']['user_key'][:4] + '••••••••••••'  # Partially mask key
            if 'telegram' in safe_config and 'bot_token' in safe_config['telegram']:
                safe_config['telegram']['bot_token'] = '••••••••••••••••'
            
            return {"status": "success", "config": safe_config}
        else:
            # Return default configuration
            default_config = {
                "email": {"enabled": False, "smtp_server": "", "smtp_port": 587, "username": "", "password": "", "to_addresses": []},
                "pushover": {"enabled": False, "user_key": "", "api_token": ""},
                "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
                "webhook": {"enabled": False, "urls": []}
            }
            return {"status": "success", "config": default_config}
    except Exception as e:
        security_logger.error(f"Failed to load notification config: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/api/notifications/config', methods=['POST'])
@login_required
@ip_whitelist_required
def api_save_notification_config():
    """API endpoint to save notification configuration"""
    try:
        new_config = request.get_json()
        if not new_config:
            return {"status": "error", "message": "No configuration data provided"}, 400
        
        config_path = '/app/logs/notification_config.json'
        
        # Ensure the logs directory exists
        os.makedirs('/app/logs', exist_ok=True)
        
        # Load existing config to preserve sensitive data if masked
        existing_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
        
        # Merge configurations, preserving masked passwords
        merged_config = existing_config.copy()
        for service, settings in new_config.items():
            if service not in merged_config:
                merged_config[service] = {}
            for key, value in settings.items():
                # Don't overwrite masked passwords
                if key == 'password' and value == '••••••••':
                    continue
                if key in ['api_token', 'user_key', 'bot_token'] and '••••' in str(value):
                    continue
                merged_config[service][key] = value
        
        # Save the configuration
        with open(config_path, 'w') as f:
            json.dump(merged_config, f, indent=2)
        
        security_logger.info(f"Notification configuration updated by {current_user.id}")
        return {"status": "success", "message": "Configuration saved successfully"}
    except Exception as e:
        security_logger.error(f"Failed to save notification config: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/api/notifications/test', methods=['POST'])
@login_required
@ip_whitelist_required
def api_test_notification_system():
    """API endpoint to test the notification system with current settings"""
    try:
        # Load current notification configuration
        config_path = '/app/logs/notification_config.json'
        if not os.path.exists(config_path):
            return {"status": "error", "message": "Notification configuration not found"}, 400
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        test_results = []
        
        # Test Pushover if enabled
        if config.get('pushover', {}).get('enabled', False):
            try:
                import requests
                pushover_config = config['pushover']
                pushover_data = {
                    'token': pushover_config['api_token'],
                    'user': pushover_config['user_key'],
                    'title': '🧪 Test Notification',
                    'message': 'This is a test notification from your Parker PO Dashboard! If you receive this, your push notifications are working correctly. 🎉',
                    'priority': 0
                }
                
                response = requests.post('https://api.pushover.net/1/messages.json', data=pushover_data, timeout=10)
                if response.status_code == 200:
                    test_results.append({"service": "Pushover", "status": "success", "message": "Test notification sent successfully"})
                else:
                    test_results.append({"service": "Pushover", "status": "error", "message": f"Failed to send: {response.text}"})
            except Exception as e:
                test_results.append({"service": "Pushover", "status": "error", "message": f"Error: {str(e)}"})
        
        # Test Email if enabled
        if config.get('email', {}).get('enabled', False):
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                email_config = config['email']
                msg = MIMEMultipart()
                msg['From'] = email_config['username']
                msg['To'] = ', '.join(email_config['to_addresses'])
                msg['Subject'] = '🧪 Test Notification - Parker PO Dashboard'
                
                body = """
                This is a test notification from your Parker PO Dashboard!
                
                If you receive this email, your email notifications are working correctly. 🎉
                
                Dashboard URL: https://192.168.0.62:5000
                Test Time: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
                server.quit()
                
                test_results.append({"service": "Email", "status": "success", "message": "Test email sent successfully"})
            except Exception as e:
                test_results.append({"service": "Email", "status": "error", "message": f"Error: {str(e)}"})
        
        if not test_results:
            return {"status": "warning", "message": "No notification services are enabled", "results": []}
        
        # Log the test
        security_logger.info(f"Notification test performed by {current_user.id}")
        
        return {
            "status": "success",
            "message": "Notification test completed",
            "results": test_results
        }
        
    except Exception as e:
        security_logger.error(f"Notification test failed: {e}")
        return {"status": "error", "message": f"Test failed: {str(e)}"}, 500

@app.route('/api/test_notification')
@login_required
@ip_whitelist_required
def api_test_notification():
    """API endpoint to test notifications (legacy endpoint)"""
    return {
        "status": "success",
        "message": "Test notification triggered",
        "data": {
            "title": "📄 Test PDF Processed!",
            "message": "PO 123456 has been successfully processed and is ready for review.",
            "type": "success",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.route('/api/filemaker/create', methods=['POST'])
@login_required
@ip_whitelist_required
def api_create_filemaker_record():
    """API endpoint to create a record in FileMaker database"""
    try:
        data = request.get_json()
        if not data or 'po_number' not in data:
            return {"status": "error", "message": "PO number is required"}, 400
        
        po_number = data['po_number']
        
        # Get PO data
        po_folder_path = os.path.join(POS_PATH, po_number)
        if not os.path.exists(po_folder_path):
            return {"status": "error", "message": f"PO {po_number} not found"}, 404
        
        # Load PO JSON data
        json_files = glob.glob(os.path.join(po_folder_path, "*.json"))
        if not json_files:
            return {"status": "error", "message": f"No JSON data found for PO {po_number}"}, 404
        
        po_data = {}
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    file_data = json.load(f)
                    po_data.update(file_data)
            except:
                continue
        
        # Initialize FileMaker integration
        try:
            from filemaker_integration import FileMakerIntegration
        except ImportError as e:
            security_logger.error(f"FileMaker integration module not found: {str(e)}")
            return {"status": "error", "message": "FileMaker integration module not available"}, 500
        
        # Load FileMaker configuration
        config_path = 'filemaker_config.json'
        if not os.path.exists(config_path):
            return {"status": "error", "message": "FileMaker configuration not found. Please configure FileMaker settings first."}, 400
        
        with open(config_path, 'r') as f:
            fm_config = json.load(f)
        
        # Check if FileMaker integration is enabled
        if not fm_config.get('enabled', True):
            return {"status": "error", "message": "FileMaker integration is currently disabled"}, 503
        
        # Create FileMaker integration instance
        protocol = "https" if fm_config['port'] == 443 else "http"
        server_url = f"{protocol}://{fm_config['server']}:{fm_config['port']}"
        
        print(f"DEBUG: Attempting to connect to FileMaker at {server_url}")
        print(f"DEBUG: Database: {fm_config['database']}, Layout: {fm_config['layout']}")
        
        fm = FileMakerIntegration(
            server_url=server_url,
            database=fm_config['database'],
            username=fm_config['username'],
            password=fm_config['password'],
            ssl_verify=fm_config.get('ssl_verify', True),
            timeout=fm_config.get('timeout', 10)
        )
        
        # Authenticate with FileMaker
        print("DEBUG: Attempting authentication...")
        auth_start_time = datetime.now()
        
        try:
            auth_result = fm.authenticate()
            auth_end_time = datetime.now()
            auth_duration = (auth_end_time - auth_start_time).total_seconds()
            
            print(f"DEBUG: Authentication took {auth_duration:.2f} seconds")
            print(f"DEBUG: Authentication result: {auth_result}")
            
            if not auth_result:
                return {"status": "error", "message": "Failed to authenticate with FileMaker server"}, 500
        except Exception as auth_error:
            auth_end_time = datetime.now()
            auth_duration = (auth_end_time - auth_start_time).total_seconds()
            print(f"DEBUG: Authentication failed after {auth_duration:.2f} seconds with error: {auth_error}")
            return {"status": "error", "message": f"FileMaker authentication error: {str(auth_error)}"}, 500
        
        # Prepare data for FileMaker using field mapping
        fm_data = {}
        
        # Check if custom data was provided from the form
        custom_data = data.get('custom_data', {})
        
        # Get PO data from JSON files (will be overridden by custom data if provided)
        po_json_data = {}
        for file_name in os.listdir(po_folder_path):
            if file_name.endswith('.json') and not file_name.startswith('.'):
                json_path = os.path.join(po_folder_path, file_name)
                try:
                    with open(json_path, 'r') as f:
                        json_content = json.load(f)
                        po_json_data.update(json_content)
                except:
                    continue
        
        # Merge custom data with original data (custom data takes priority)
        merged_data = {**po_json_data, **custom_data}
        
        # Log what data we're using
        if custom_data:
            print(f"DEBUG: Using custom form data for PO {po_number}")
            print(f"DEBUG: Custom data: {custom_data}")
        
        # Map fields from merged data to FileMaker
        for local_field, fm_field in fm_config['field_mapping'].items():
            if local_field == 'po_number':
                fm_data[fm_field] = merged_data.get('purchase_order_number', po_number)
            elif local_field == 'part_number':
                fm_data[fm_field] = merged_data.get('part_number', '')
            elif local_field == 'quantity':
                fm_data[fm_field] = merged_data.get('quantity', '')
            elif local_field == 'mjo_number':
                fm_data[fm_field] = merged_data.get('production_order', '')
            elif local_field == 'delivery_date':
                fm_data[fm_field] = merged_data.get('dock_date', '')
            elif local_field == 'planner_name':
                fm_data[fm_field] = merged_data.get('buyer_name', '')
        
        # Create record in FileMaker
        record_id = fm.create_record(fm_data, fm_config['layout'], fm_config)
        
        if record_id:
            if record_id == "DUPLICATE_SKIP":
                # Handle the case where PO already exists
                security_logger.info(f"FileMaker record for PO {po_number} already exists (duplicate skipped) by {current_user.id}")
                return {
                    "status": "warning", 
                    "message": f"PO {po_number} already exists in FileMaker database. This is normal if the PO was processed before.",
                    "record_id": "existing"
                }, 200
            else:
                # Log the successful creation or update
                action = "updated" if isinstance(record_id, str) and record_id.startswith("updated_") else "created"
                security_logger.info(f"FileMaker record {action} for PO {po_number} by {current_user.id}")
                return {
                    "status": "success", 
                    "message": f"Record {action} successfully in FileMaker", 
                    "record_id": record_id
                }, 200
        else:
            return {"status": "error", "message": "Failed to create record in FileMaker"}, 500
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        security_logger.error(f"FileMaker record creation failed for PO {po_number}: {str(e)}")
        security_logger.error(f"Full traceback: {error_details}")
        print(f"FileMaker Error: {str(e)}")
        print(f"Full traceback: {error_details}")
        return {"status": "error", "message": f"FileMaker error: {str(e)}"}, 500
            
    except Exception as e:
        security_logger.error(f"FileMaker record creation failed: {e}")
        return {"status": "error", "message": f"Error creating FileMaker record: {str(e)}"}, 500

@app.route('/api/filemaker/config', methods=['GET'])
@login_required
@ip_whitelist_required
def api_get_filemaker_config():
    """API endpoint to get FileMaker configuration"""
    try:
        config_path = '/app/logs/filemaker_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Mask sensitive data
            safe_config = config.copy()
            if 'filemaker' in safe_config and 'password' in safe_config['filemaker']:
                safe_config['filemaker']['password'] = '••••••••'
            
            return {"status": "success", "config": safe_config}
        else:
            # Return default configuration
            default_config = {
                "filemaker": {
                    "server_url": "https://your-filemaker-server.com",
                    "database": "PO_Management",
                    "username": "api_user",
                    "password": "",
                    "layout_name": "PO_Processing"
                },
                "field_mapping": {
                    "PO_Number": "po_number",
                    "Vendor": "vendor",
                    "Total_Amount": "total_amount",
                    "PO_Date": "date",
                    "Status": "Processed",
                    "Source_System": "Parker_PO_OCR"
                },
                "auto_sync": False,
                "sync_interval_minutes": 60
            }
            return {"status": "success", "config": default_config}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/api/filemaker/config', methods=['POST'])
@login_required
@ip_whitelist_required
def api_save_filemaker_config():
    """API endpoint to save FileMaker configuration"""
    try:
        new_config = request.get_json()
        if not new_config:
            return {"status": "error", "message": "No configuration data provided"}, 400
        
        config_path = '/app/logs/filemaker_config.json'
        
        # Ensure the logs directory exists
        os.makedirs('/app/logs', exist_ok=True)
        
        # Load existing config to preserve sensitive data if masked
        existing_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
        
        # Merge configurations, preserving masked passwords
        merged_config = existing_config.copy()
        merged_config.update(new_config)
        
        # Don't overwrite masked passwords
        if (new_config.get('filemaker', {}).get('password') == '••••••••' and 
            existing_config.get('filemaker', {}).get('password')):
            merged_config['filemaker']['password'] = existing_config['filemaker']['password']
        
        # Save the configuration
        with open(config_path, 'w') as f:
            json.dump(merged_config, f, indent=2)
        
        security_logger.info(f"FileMaker configuration updated by {current_user.id}")
        return {"status": "success", "message": "Configuration saved successfully"}
    except Exception as e:
        security_logger.error(f"Failed to save FileMaker config: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/api/filemaker/export_pdf/<record_id>')
@login_required
@ip_whitelist_required
def api_export_filemaker_pdf(record_id):
    """API endpoint to export a FileMaker record as PDF"""
    try:
        # Initialize FileMaker integration
        try:
            from filemaker_integration import FileMakerIntegration
        except ImportError as e:
            security_logger.error(f"FileMaker integration module not found: {str(e)}")
            return {"status": "error", "message": "FileMaker integration module not available"}, 500
        
        # Load FileMaker configuration
        config_path = 'filemaker_config.json'
        if not os.path.exists(config_path):
            return {"status": "error", "message": "FileMaker configuration not found. Please configure FileMaker settings first."}, 400
        
        with open(config_path, 'r') as f:
            fm_config = json.load(f)
        
        # Check if FileMaker integration is enabled
        if not fm_config.get('enabled', False):
            return {"status": "error", "message": "FileMaker integration is currently disabled"}, 503
        
        # Create FileMaker integration instance
        server_url = f"https://{fm_config['server']}:{fm_config['port']}"
        database = fm_config['database']
        username = fm_config['username']
        password = fm_config['password']
        layout = fm_config['layout']
        
        fm = FileMakerIntegration(
            server_url=server_url,
            database=database,
            username=username,
            password=password,
            ssl_verify=fm_config.get('ssl_verify', True)
        )
        
        # Authenticate with FileMaker
        try:
            auth_success = fm.authenticate()
            if not auth_success:
                return {"status": "error", "message": "Failed to authenticate with FileMaker server"}, 500
        except Exception as auth_error:
            security_logger.error(f"FileMaker authentication failed: {str(auth_error)}")
            return {"status": "error", "message": f"FileMaker authentication error: {str(auth_error)}"}, 500
        
        # Export the record as PDF using simplified script (no parameters needed)
        pdf_result = fm.export_record_as_pdf(record_id, layout)
        
        if pdf_result:
            # Log successful export
            security_logger.info(f"PDF export successful for record {record_id} by {current_user.id}")
            
            # The script saves PDF to server, return success message with file info
            return {
                "status": "success", 
                "message": f"PDF exported successfully for record {record_id}",
                "file_info": pdf_result,
                "note": "PDF saved to FileMaker Server Documents folder"
            }
        else:
            return {"status": "error", "message": "Failed to export PDF"}, 500
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        security_logger.error(f"PDF export failed for record {record_id}: {str(e)}")
        security_logger.error(f"Full traceback: {error_details}")
        return {"status": "error", "message": f"PDF export error: {str(e)}"}, 500

@app.route('/api/filemaker/record/<record_id>')
@login_required
@ip_whitelist_required
def api_get_filemaker_record(record_id):
    """API endpoint to get a FileMaker record for export preview"""
    try:
        # Initialize FileMaker integration
        try:
            from filemaker_integration import FileMakerIntegration
        except ImportError as e:
            return {"status": "error", "message": "FileMaker integration module not available"}, 500
        
        # Load FileMaker configuration
        config_path = 'filemaker_config.json'
        if not os.path.exists(config_path):
            return {"status": "error", "message": "FileMaker configuration not found"}, 400
        
        with open(config_path, 'r') as f:
            fm_config = json.load(f)
        
        # Create FileMaker integration instance
        fm = FileMakerIntegration(
            server_url=fm_config['filemaker']['server_url'],
            database=fm_config['filemaker']['database'],
            username=fm_config['filemaker']['username'],
            password=fm_config['filemaker']['password'],
            layout=fm_config['layout'],
            ssl_verify=fm_config.get('ssl_verify', True)
        )
        
        # Authenticate and get record
        if fm.authenticate():
            record_data = fm.get_record_for_export(record_id)
            if record_data:
                return {"status": "success", "data": record_data}
            else:
                return {"status": "error", "message": "Record not found"}, 404
        else:
            return {"status": "error", "message": "Authentication failed"}, 500
            
    except Exception as e:
        security_logger.error(f"Failed to get record {record_id}: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/api/restart')
@login_required
@ip_whitelist_required
@limiter.limit("2 per hour")
def api_restart():
    """API endpoint to restart container"""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(CONTAINER_NAME)
            container.restart()
            security_logger.info(f"Container restart initiated by {current_user.id} from {request.remote_addr}")
            return {"status": "success", "message": "Container restarted"}
        else:
            return {"status": "error", "message": "Docker not available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('/app/logs', exist_ok=True)
    
    # Check if HTTPS is enabled and certificates exist
    use_https = os.getenv('USE_HTTPS', 'true').lower() == 'true'
    ssl_cert = os.getenv('SSL_CERT_PATH', '/app/ssl/dashboard.crt')
    ssl_key = os.getenv('SSL_KEY_PATH', '/app/ssl/dashboard.key')
    
    if use_https and ssl_cert and ssl_key and os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        try:
            print("🔒 Starting secure dashboard with HTTPS...")
            print(f"🔗 Access at: https://192.168.0.62:9443")
            print("⚠️  Browser will show security warning (normal for self-signed certificates)")
            print("   Click 'Advanced' → 'Proceed to 192.168.0.62 (unsafe)' to continue")
            print("")
            print(f"Debug: SSL cert path: {ssl_cert}")
            print(f"Debug: SSL key path: {ssl_key}")
            print(f"Debug: Certificate exists: {os.path.exists(ssl_cert)}")
            print(f"Debug: Key exists: {os.path.exists(ssl_key)}")
            app.run(host='0.0.0.0', port=9443, ssl_context=(ssl_cert, ssl_key), debug=app.config['DEBUG'])
        except Exception as e:
            print(f"❌ HTTPS startup failed: {e}")
            print("🔄 Falling back to HTTP mode...")
            print(f"🔗 Access at: http://192.168.0.62:9443")
            app.run(host='0.0.0.0', port=9443, debug=app.config['DEBUG'])
    else:
        if use_https:
            print("⚠️  HTTPS enabled but SSL certificates not found. Starting in HTTP mode.")
        print("🔓 Starting dashboard in HTTP mode...")
        print(f"🔗 Access at: http://192.168.0.62:9443")
        print("⚠️  Warning: HTTP mode is not secure for internet exposure!")
        app.run(host='0.0.0.0', port=9443, debug=app.config['DEBUG'])

# Dashboard Web Server
from flask import Flask, render_template, jsonify, send_file, request
import docker
import json
import os
import glob
import requests
from datetime import datetime, timedelta
import subprocess
import psutil
import time
from pathlib import Path
from notifications import notification_manager

app = Flask(__name__)

# Configuration
BASE_PATH = "/volume1/Main/Main/ParkerPOsOCR"
SCANS_PATH = f"{BASE_PATH}/Scans"
POS_PATH = f"{BASE_PATH}/POs"
ARCHIVE_PATH = f"{BASE_PATH}/Archive"
ERRORS_PATH = f"{BASE_PATH}/Errors"
LOG_PATH = f"{POS_PATH}/po_processor.log"
CONTAINER_NAME = "po-processor"

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
            "started_at": container.attrs['State']['StartedAt'],
            "restart_policy": container.attrs['HostConfig']['RestartPolicy']['Name'],
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
            "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
            "memory_percent": round(memory_percent, 2),
            "uptime": container.attrs['State']['StartedAt']
        }
    except docker.errors.NotFound:
        return {"status": "not_found", "message": "Container not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_processing_stats():
    """Get processing statistics"""
    stats = {
        "files_in_queue": len([f for f in os.listdir(SCANS_PATH) if f.endswith('.pdf')]) if os.path.exists(SCANS_PATH) else 0,
        "completed_pos": 0,
        "error_files": len([f for f in os.listdir(ERRORS_PATH) if f.endswith('.pdf')]) if os.path.exists(ERRORS_PATH) else 0,
        "archived_files": len([f for f in os.listdir(ARCHIVE_PATH) if f.endswith('.pdf')]) if os.path.exists(ARCHIVE_PATH) else 0,
        "total_processed": 0
    }
    
    # Count PO folders
    if os.path.exists(POS_PATH):
        po_folders = [d for d in os.listdir(POS_PATH) if os.path.isdir(os.path.join(POS_PATH, d)) and d.startswith('455')]
        stats["completed_pos"] = len(po_folders)
    
    stats["total_processed"] = stats["completed_pos"] + stats["error_files"]
    
    return stats

def get_recent_activity():
    """Get recent processing activity from logs"""
    activities = []
    
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()
                
            # Get last 20 log entries
            for line in lines[-20:]:
                if 'INFO' in line or 'ERROR' in line:
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
        except Exception as e:
            activities.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "level": "ERROR",
                "message": f"Failed to read log: {e}"
            })
    
    return activities[-10:]  # Return last 10 activities

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
        disk_usage = psutil.disk_usage(BASE_PATH)
        health["disk_usage"] = {
            "total_gb": round(disk_usage.total / 1024**3, 2),
            "used_gb": round(disk_usage.used / 1024**3, 2),
            "free_gb": round(disk_usage.free / 1024**3, 2),
            "percent": round((disk_usage.used / disk_usage.total) * 100, 2)
        }
    except Exception as e:
        health["disk_usage"] = {"error": str(e)}
    
    # Get system uptime
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        health["uptime"] = uptime_str
    except Exception:
        health["uptime"] = "Unknown"
    
    # Get Docker version
    try:
        client = get_docker_client()
        if client:
            health["docker_version"] = client.version()['Version']
    except Exception:
        health["docker_version"] = "Unknown"
    
    return health

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API endpoint for container status"""
    return jsonify(get_container_status())

@app.route('/api/stats')
def api_stats():
    """API endpoint for processing statistics"""
    return jsonify(get_processing_stats())

@app.route('/api/activity')
def api_activity():
    """API endpoint for recent activity"""
    return jsonify(get_recent_activity())

@app.route('/api/completed')
def api_completed():
    """API endpoint for completed files"""
    return jsonify(get_completed_files())

@app.route('/api/health')
def api_health():
    """API endpoint for system health"""
    return jsonify(get_system_health())

@app.route('/api/logs')
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

@app.route('/api/json/<path:filename>')
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
        

        # If there's a main JSON file, flatten and expose all relevant fields at the top level
        main_json = next((j for j in json_files if j["name"] == f"{po_number}_info.json" or j["name"] == f"{po_number}.json"), None)
        if main_json and isinstance(main_json["content"], dict):
            for key, value in main_json["content"].items():
                po_details[key] = value

        # Ensure all expected fields are present (for modal population)
        for field in ["part_number", "quantity", "buyer_name", "dock_date", "production_order"]:
            if field not in po_details:
                po_details[field] = "N/A"

        return po_details
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/po/<po_number>/download')
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

@app.route('/api/restart')
def api_restart():
    """API endpoint to restart container"""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(CONTAINER_NAME)
            container.restart()
            return {"status": "success", "message": "Container restarted"}
        else:
            return {"status": "error", "message": "Docker not available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/api/notifications/config', methods=['GET', 'POST'])
def api_notifications_config():
    """Get or update notification configuration"""
    if request.method == 'GET':
        return jsonify({"status": "success", "config": notification_manager.config})
    
    elif request.method == 'POST':
        try:
            new_config = request.get_json()
            notification_manager.config = new_config
            notification_manager.save_config()
            return jsonify({"status": "success", "message": "Configuration updated"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

@app.route('/api/notifications/test', methods=['POST'])
def api_test_notification():
    """Test notification system"""
    try:
        data = request.get_json() or {}
        title = data.get('title', 'Test Notification')
        message = data.get('message', 'This is a test notification from the PO processing system.')
        
        results = notification_manager.send_notification(title, message, None, "test")
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/notifications/send', methods=['POST'])
def api_send_notification():
    """Send a custom notification"""
    try:
        data = request.get_json()
        title = data.get('title', 'PO Processing Alert')
        message = data.get('message', '')
        po_number = data.get('po_number')
        notification_type = data.get('type', 'info')
        
        results = notification_manager.send_notification(title, message, po_number, notification_type)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/filemaker/create', methods=['POST'])
def api_filemaker_create():
    """Directly create a FileMaker record for a PO"""
    try:
        data = request.get_json()
        if not data or 'po_number' not in data:
            return jsonify({"success": False, "error": "PO number is required"}), 400
        
        po_number = data['po_number']
        force_resubmit = data.get('force_resubmit', False)
        
        # Build the command with force parameter if needed
        cmd = ['docker', 'exec', 'po-processor', 'python', '/app/submit_to_filemaker.py', po_number]
        if force_resubmit:
            cmd.append('--force')
        
        # Call the submit_to_filemaker.py script directly inside the Docker container
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Success
            return jsonify({"success": True, "message": f"FileMaker record created for PO {po_number}"})
        else:
            # Error
            error_message = result.stderr.strip() if result.stderr else result.stdout.strip()
            return jsonify({"success": False, "error": error_message or "Unknown error from script"}), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "FileMaker submission timed out"}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": f"Script execution failed: {e}"}), 500
    except Exception as e:
        app.logger.error(f"Error in FileMaker create: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/pending-approvals')
def api_pending_approvals():
    """Get POs that are pending FileMaker approval"""
    try:
        pending_pos = []
        
        # Look through all PO folders
        if os.path.exists(POS_PATH):
            for po_folder in os.listdir(POS_PATH):
                po_folder_path = os.path.join(POS_PATH, po_folder)
                if os.path.isdir(po_folder_path):
                    # Look for the main JSON file
                    json_file = os.path.join(po_folder_path, f"{po_folder}_info.json")
                    if os.path.exists(json_file):
                        try:
                            with open(json_file, 'r') as f:
                                po_data = json.load(f)
                            
                            # Check if this PO is pending approval
                            if (po_data.get('ready_for_filemaker') and 
                                po_data.get('approval_status') == 'pending' and 
                                not po_data.get('filemaker_submitted')):
                                
                                pending_pos.append({
                                    "po_number": po_folder,
                                    "vendor_name": po_data.get('vendor_name', 'Unknown'),
                                    "po_total": po_data.get('po_total', 'Unknown'),
                                    "quantity": po_data.get('quantity', 'Unknown'),
                                    "dock_date": po_data.get('dock_date', 'Unknown'),
                                    "processed_timestamp": po_data.get('processed_timestamp', 'Unknown'),
                                    "json_file": json_file
                                })
                        except Exception as e:
                            print(f"Error reading {json_file}: {e}")
        
        return {"pending_approvals": pending_pos, "count": len(pending_pos)}
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/po/<po_number>/approve-filemaker', methods=['POST'])
def api_approve_filemaker(po_number):
    """Approve a PO for FileMaker submission"""
    try:
        # Call the submission script
        script_path = "/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts/submit_to_filemaker.py"
        
        # Run the script inside the Docker container
        client = get_docker_client()
        if not client:
            return {"error": "Docker not available"}, 500
        
        try:
            container = client.containers.get(CONTAINER_NAME)
            
            # Execute the submission script
            result = container.exec_run(
                f"python /app/submit_to_filemaker.py {po_number}",
                workdir="/app"
            )
            
            output = result.output.decode('utf-8').strip()
            
            if result.exit_code == 0:
                # Success
                return {
                    "status": "success", 
                    "message": f"PO {po_number} successfully submitted to FileMaker",
                    "output": output
                }
            else:
                # Error
                return {
                    "status": "error", 
                    "message": f"FileMaker submission failed: {output}",
                    "exit_code": result.exit_code
                }, 400
                
        except docker.errors.NotFound:
            return {"error": f"Container {CONTAINER_NAME} not found"}, 500
        except Exception as e:
            return {"error": f"Container execution error: {str(e)}"}, 500
            
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    ssl_context = ('ssl/dashboard.crt', 'ssl/dashboard.key')
    app.run(host='0.0.0.0', port=9443, debug=False, ssl_context=ssl_context)

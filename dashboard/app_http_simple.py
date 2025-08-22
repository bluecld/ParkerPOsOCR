# Simple HTTP Dashboard - No HTTPS, No Auth
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

app = Flask(__name__)

# Configuration
BASE_PATH = "/app"
POS_PATH = f"{BASE_PATH}/POs"
SCANS_PATH = f"{BASE_PATH}/Scans"
ARCHIVE_PATH = f"{BASE_PATH}/Archive"
ERRORS_PATH = f"{BASE_PATH}/Errors"
CONTAINER_NAME = "po-processor"

def get_docker_client():
    """Get Docker client"""
    try:
        return docker.from_env()
    except Exception as e:
        print(f"Docker connection error: {e}")
        return None

def get_po_info(po_folder):
    """Get PO information from JSON file"""
    try:
        info_file = os.path.join(po_folder, f"{os.path.basename(po_folder)}_info.json")
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error reading PO info: {e}")
        return None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/login')
def login():
    """Login page (no authentication required for HTTP version)"""
    return dashboard()

@app.route('/api/status')
def api_status():
    """Get processing status"""
    try:
        # Count files in different folders
        scans_count = len([f for f in os.listdir(SCANS_PATH) if f.endswith('.pdf')]) if os.path.exists(SCANS_PATH) else 0
        pos_count = len(os.listdir(POS_PATH)) if os.path.exists(POS_PATH) else 0
        errors_count = len(os.listdir(ERRORS_PATH)) if os.path.exists(ERRORS_PATH) else 0
        
        return jsonify({
            'scans_pending': scans_count,
            'pos_processed': pos_count,
            'errors': errors_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/po/<po_number>')
def api_po_details(po_number):
    """Get PO details"""
    try:
        po_folder = os.path.join(POS_PATH, po_number)
        if not os.path.exists(po_folder):
            return jsonify({'error': f'PO {po_number} not found'}), 404
        
        po_info = get_po_info(po_folder)
        if not po_info:
            return jsonify({'error': f'PO {po_number} info not available'}), 404
        
        return jsonify(po_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/completed')
def api_completed():
    """Get completed POs"""
    try:
        pos = []
        if os.path.exists(POS_PATH):
            for po_folder in os.listdir(POS_PATH):
                po_path = os.path.join(POS_PATH, po_folder)
                if os.path.isdir(po_path):
                    po_info = get_po_info(po_path)
                    if po_info:
                        pos.append({
                            'po_number': po_folder,
                            'purchase_order_number': po_info.get('purchase_order_number', 'N/A'),
                            'part_number': po_info.get('part_number', 'N/A'),
                            'revision': po_info.get('revision', 'N/A'),
                            'timestamp': po_info.get('processed_timestamp', 'N/A')
                        })
        
        return jsonify({'pos': pos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity')
def api_activity():
    """Get recent activity"""
    try:
        # For now, return basic activity log
        activities = []
        
        # Check recent POs
        if os.path.exists(POS_PATH):
            po_folders = [os.path.join(POS_PATH, d) for d in os.listdir(POS_PATH) 
                         if os.path.isdir(os.path.join(POS_PATH, d))]
            po_folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            for po_folder in po_folders[:10]:  # Last 10 POs
                po_number = os.path.basename(po_folder)
                po_info = get_po_info(po_folder)
                if po_info:
                    activities.append({
                        'type': 'po_processed',
                        'message': f'PO {po_number} processed successfully',
                        'timestamp': po_info.get('processed_timestamp', 'N/A'),
                        'po_number': po_number
                    })
        
        return jsonify({'activities': activities})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/send', methods=['POST'])
def receive_notification():
    """Receive notifications from the processor"""
    try:
        data = request.get_json()
        print(f"Received notification: {data}")
        
        # Just acknowledge receipt for now
        return jsonify({'status': 'received', 'message': 'Notification processed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting HTTP Dashboard on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)

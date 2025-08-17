#!/usr/bin/env python3
"""
Create export folder on Mac FileMaker Server using Python SSH
"""

import subprocess
import sys

def create_export_folder():
    """Create the export folder on Mac via SSH"""
    print("=== Creating Export Folder on Mac FileMaker Server ===")
    
    host = "192.168.0.108"
    username = "admin"
    password = "Rynrin12"
    
    commands = [
        "mkdir -p /Users/Shared/ParkerPOsOCR/exports",
        "chmod 755 /Users/Shared/ParkerPOsOCR/exports", 
        "ls -la /Users/Shared/ParkerPOsOCR/",
        "whoami",
        "pwd"
    ]
    
    for cmd in commands:
        print(f"\nExecuting: {cmd}")
        try:
            # Try using subprocess with echo for password
            full_cmd = f'echo "{password}" | ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {username}@{host} "{cmd}"'
            print(f"Command: {full_cmd}")
            
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f"Return code: {result.returncode}")
            if result.stdout:
                print(f"Output: {result.stdout}")
            if result.stderr:
                print(f"Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("Command timed out")
        except Exception as e:
            print(f"Error executing command: {str(e)}")

def test_folder_via_filemaker():
    """Test folder creation via FileMaker script"""
    print("\n=== Testing Folder via FileMaker Script ===")
    
    import sys
    import os
    sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')
    
    from filemaker_integration import FileMakerIntegration
    import json
    import requests
    import urllib3
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Load config
    with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
        config = json.load(f)
    
    # Create FileMaker integration instance
    server_url = f"https://{config['server']}:{config['port']}"
    fm = FileMakerIntegration(
        server_url=server_url,
        database=config['database'],
        username=config['username'],
        password=config['password'],
        ssl_verify=config.get('ssl_verify', False),
        timeout=config.get('timeout', 30)
    )
    
    # Authenticate
    if not fm.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("✅ Authentication successful!")
    headers = fm.get_headers()
    
    # Test with different export paths
    test_paths = [
        "/tmp/test_export.pdf",  # Temporary folder
        "/Users/Shared/test_export.pdf",  # Shared folder
        "/Users/Shared/ParkerPOsOCR/exports/test_export.pdf",  # Target folder
    ]
    
    records_url = f"{server_url}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records"
    
    for path in test_paths:
        print(f"\nTesting export path: {path}")
        
        test_data = {
            "script": "PDFTimesheet",
            "script.param": path,
            "fieldData": {}
        }
        
        try:
            response = requests.post(records_url, json=test_data, headers=headers, verify=False, timeout=30)
            result = response.json()
            script_error = result.get('response', {}).get('scriptError', 'unknown')
            
            print(f"Status: {response.status_code}")
            print(f"Script Error: {script_error}")
            
            if script_error == "0":
                print(f"✅ SUCCESS! Path works: {path}")
                break
            elif script_error == "800":
                print(f"❌ Error 800 - Path issue: {path}")
            else:
                print(f"❌ Other error: {script_error}")
                
        except Exception as e:
            print(f"❌ Request error: {str(e)}")

if __name__ == "__main__":
    create_export_folder()
    test_folder_via_filemaker()

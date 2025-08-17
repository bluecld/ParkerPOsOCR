#!/usr/bin/env python3
"""
Test script to verify export folder and attempt folder creation via FileMaker
"""

import requests
import json
import urllib3
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load configuration
with open('filemaker_config.json', 'r') as f:
    config = json.load(f)

def get_auth_token():
    """Get authentication token from FileMaker"""
    auth_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/sessions"
    
    auth_data = {
        "username": config['username'],
        "password": config['password']
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            auth_url, 
            json=auth_data, 
            headers=headers, 
            verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            token = response.json()['response']['token']
            print(f"✅ Authentication successful. Token: {token[:20]}...")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def test_folder_creation_script():
    """Test a simple script to create the export folder"""
    token = get_auth_token()
    if not token:
        return
    
    # Create a simple AppleScript to create the folder
    folder_script = '''
    set exportPath to "/Users/Shared/ParkerPOsOCR/exports/"
    
    tell application "System Events"
        if not (exists folder exportPath) then
            do shell script "mkdir -p " & quoted form of exportPath
            return "Folder created: " & exportPath
        else
            return "Folder exists: " & exportPath
        end if
    end tell
    '''
    
    script_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/script/CreateExportFolder"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    script_data = {
        "script": "CreateExportFolder",
        "script.param": folder_script
    }
    
    try:
        response = requests.post(
            script_url,
            json=script_data,
            headers=headers,
            verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        print(f"Script response status: {response.status_code}")
        print(f"Script response: {response.text}")
        
    except Exception as e:
        print(f"❌ Script execution error: {str(e)}")

def test_simple_file_creation():
    """Test creating a simple file via FileMaker script"""
    token = get_auth_token()
    if not token:
        return
    
    # Test with a very simple script parameter
    test_script_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/script/TestFileCreation"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file_path = f"/Users/Shared/test_file_{timestamp}.txt"
    
    script_data = {
        "script": "TestFileCreation",
        "script.param": test_file_path
    }
    
    try:
        response = requests.post(
            test_script_url,
            json=script_data,
            headers=headers,
            verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        print(f"File creation test status: {response.status_code}")
        print(f"File creation response: {response.text}")
        
    except Exception as e:
        print(f"❌ File creation test error: {str(e)}")

if __name__ == "__main__":
    print("=== FileMaker Folder and File Creation Test ===")
    print(f"Target export path: {config['export_settings']['mac_export_path']}")
    print()
    
    print("1. Testing folder creation script...")
    test_folder_creation_script()
    print()
    
    print("2. Testing simple file creation...")
    test_simple_file_creation()
    print()
    
    print("=== Test Complete ===")

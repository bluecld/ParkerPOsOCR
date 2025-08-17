#!/usr/bin/env python3
"""
Get FileMaker Server system information and test basic file operations
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
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def get_server_info():
    """Get FileMaker Server product information"""
    try:
        info_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/productInfo"
        
        response = requests.get(
            info_url,
            verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            info = response.json()
            print("=== FileMaker Server Information ===")
            for key, value in info.get('response', {}).get('productInfo', {}).items():
                print(f"{key}: {value}")
            print()
            return info
        else:
            print(f"❌ Failed to get server info: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Server info error: {str(e)}")
        return None

def test_minimal_script():
    """Test with the most minimal script possible"""
    token = get_auth_token()
    if not token:
        return
    
    # Try to run a script that just returns a value
    script_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/script/PDFTimesheet"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Try with minimal parameters
    minimal_params = {
        "script": "PDFTimesheet",
        "script.param": "test"
    }
    
    try:
        print("Testing PDFTimesheet script with minimal parameters...")
        response = requests.post(
            script_url,
            json=minimal_params,
            headers=headers,
            verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check for script error specifically
        if 'response' in result and 'scriptError' in result['response']:
            script_error = result['response']['scriptError']
            print(f"Script Error Code: {script_error}")
            
            if script_error == "800":
                print("❌ Error 800 - This typically means:")
                print("   - File/folder doesn't exist")
                print("   - No write permissions")
                print("   - Invalid path format")
                print("   - Script parameter format issue")
        
        return result
        
    except Exception as e:
        print(f"❌ Minimal script test error: {str(e)}")
        return None

def test_script_without_params():
    """Test script without any parameters"""
    token = get_auth_token()
    if not token:
        return
    
    # Try script with no parameters at all
    script_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/script/PDFTimesheet"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    no_params = {
        "script": "PDFTimesheet"
    }
    
    try:
        print("Testing PDFTimesheet script with NO parameters...")
        response = requests.post(
            script_url,
            json=no_params,
            headers=headers,
            verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ No params script test error: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== FileMaker Server Diagnostics ===")
    print()
    
    # Get server information
    get_server_info()
    
    # Test script with minimal params
    test_minimal_script()
    print()
    
    # Test script with no params
    test_script_without_params()
    print()
    
    print("=== Diagnostics Complete ===")

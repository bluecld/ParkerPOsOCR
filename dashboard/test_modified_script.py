#!/usr/bin/env python3
"""
Test the modified PDFTimesheet script with folder parameter
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
    
    # Use Basic Authentication header instead of JSON body
    import base64
    credentials = f"{config['username']}:{config['password']}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            auth_url, 
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

def test_script_with_folder_param():
    """Test the PDFTimesheet script with folder parameter"""
    token = get_auth_token()
    if not token:
        return
    
    # Use records endpoint instead of script endpoint
    records_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test with custom folder path
    folder_path = "/Users/Shared/ParkerPOsOCR/exports/"
    
    script_data = {
        "script": "PDFTimesheet",
        "script.param": folder_path,
        "fieldData": {}  # Required for records endpoint
    }
    
    try:
        print(f"Testing PDFTimesheet script with folder: {folder_path}")
        response = requests.post(
            records_url,
            json=script_data,
            headers=headers,
            verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check for script result
        if 'response' in result and 'scriptResult' in result['response']:
            script_result = result['response']['scriptResult']
            print(f"✅ Script Result (file path): {script_result}")
        
        # Check for script error
        if 'response' in result and 'scriptError' in result['response']:
            script_error = result['response']['scriptError']
            if script_error != "0":
                print(f"❌ Script Error: {script_error}")
            else:
                print("✅ Script executed successfully (no errors)")
        
        return result
        
    except Exception as e:
        print(f"❌ Script test error: {str(e)}")
        return None

def test_script_with_different_folders():
    """Test script with different folder locations"""
    test_folders = [
        "/Users/Shared/ParkerPOsOCR/exports/",
        "/Users/Shared/",
        "/tmp/",
        "/Users/Shared/ParkerPOsOCR/test/"
    ]
    
    for folder in test_folders:
        print(f"\n--- Testing folder: {folder} ---")
        
        token = get_auth_token()
        if not token:
            continue
        
        # Use records endpoint
        records_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        script_data = {
            "script": "PDFTimesheet",
            "script.param": folder,
            "fieldData": {}  # Required for records endpoint
        }
        
        try:
            response = requests.post(
                records_url,
                json=script_data,
                headers=headers,
                verify=config.get('ssl_verify', False),
                timeout=config.get('timeout', 30)
            )
            
            result = response.json()
            
            if 'response' in result:
                script_error = result['response'].get('scriptError', 'Unknown')
                script_result = result['response'].get('scriptResult', 'No result')
                
                if script_error == "0":
                    print(f"✅ Success - File: {script_result}")
                else:
                    print(f"❌ Error {script_error} - {script_result}")
            
        except Exception as e:
            print(f"❌ Error testing {folder}: {str(e)}")

if __name__ == "__main__":
    print("=== Testing Modified PDFTimesheet Script ===")
    print()
    
    print("1. Testing with configured export folder...")
    test_script_with_folder_param()
    print()
    
    print("2. Testing with multiple folder locations...")
    test_script_with_different_folders()
    print()
    
    print("=== Test Complete ===")

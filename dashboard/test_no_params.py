#!/usr/bin/env python3
"""
Test the simplified FileMaker script that requires no parameters
"""

import requests
import json
import urllib3
import base64
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load configuration
with open('filemaker_config.json', 'r') as f:
    config = json.load(f)

def get_auth_token():
    """Get authentication token using correct method"""
    auth_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/sessions"
    
    credentials = f"{config['username']}:{config['password']}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(auth_url, headers=headers, verify=False, timeout=30)
    
    if response.status_code == 200:
        return response.json()['response']['token']
    return None

def test_simplified_script():
    """Test the PDFTimesheet script with no parameters"""
    print("Testing Simplified PDFTimesheet Script")
    print("=" * 40)
    
    token = get_auth_token()
    if not token:
        print("Authentication failed")
        return False
    
    print("Authentication successful")
    
    records_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test script with NO parameters
    script_data = {
        "script": "PDFTimesheet",
        "fieldData": {}  # Required for records endpoint
    }
    
    print("Executing PDFTimesheet script with no parameters...")
    
    try:
        response = requests.post(
            records_url,
            json=script_data,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            script_error = result.get('response', {}).get('scriptError', 'unknown')
            script_result = result.get('response', {}).get('scriptResult', 'no result')
            record_id = result.get('response', {}).get('recordId', 'unknown')
            
            print(f"Record ID: {record_id}")
            print(f"Script Error Code: {script_error}")
            print(f"Script Result: {script_result}")
            
            if script_error == "0":
                print("SUCCESS! Script executed without errors!")
                print(f"PDF Export Result: {script_result}")
                return True
            else:
                print(f"Script Error {script_error}")
                print(f"Error Details: {script_result}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing FileMaker PDF Export with Simplified Script")
    print("=" * 60)
    
    success = test_simplified_script()
    
    print("\n" + "=" * 60)
    print("FINAL RESULT:")
    print(f"Test: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print("PDF export is working!")
    else:
        print("Check FileMaker script configuration")
        
    print("=" * 60)

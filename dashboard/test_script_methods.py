#!/usr/bin/env python3
"""
Test correct FileMaker Data API script execution syntax
"""

import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

from filemaker_integration import FileMakerIntegration
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_script_execution_methods():
    """Test different ways to execute FileMaker scripts via Data API"""
    
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
    
    print("\n=== Testing Different Script Execution Methods ===")
    
    # Method 1: POST to script endpoint (what we tried)
    print("\n1. Testing POST to /script/PDFTimesheet endpoint...")
    script_url_1 = f"{server_url}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/script/PDFTimesheet"
    test_data_1 = {
        "script": "PDFTimesheet",
        "script.param": "/Users/Shared/ParkerPOsOCR/exports/test.pdf"
    }
    
    try:
        response = requests.post(script_url_1, json=test_data_1, headers=headers, verify=False, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Method 2: POST to records endpoint with script parameter
    print("\n2. Testing POST to records endpoint with script...")
    records_url = f"{server_url}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records"
    test_data_2 = {
        "script": "PDFTimesheet",
        "script.param": "/Users/Shared/ParkerPOsOCR/exports/test.pdf",
        "fieldData": {}
    }
    
    try:
        response = requests.post(records_url, json=test_data_2, headers=headers, verify=False, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Method 3: GET request with script parameters
    print("\n3. Testing GET to records with script parameters...")
    get_params = {
        'script': 'PDFTimesheet',
        'script.param': '/Users/Shared/ParkerPOsOCR/exports/test.pdf'
    }
    
    try:
        response = requests.get(records_url, params=get_params, headers=headers, verify=False, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Method 4: Check if we need to run script with a specific record
    print("\n4. Testing script execution with existing record...")
    
    # First, get a record
    try:
        get_response = requests.get(records_url, headers=headers, verify=False, timeout=30)
        if get_response.status_code == 200:
            records_data = get_response.json()
            records = records_data.get('response', {}).get('data', [])
            
            if records:
                record_id = records[0]['recordId']
                print(f"Found record ID: {record_id}")
                
                # Try running script on specific record
                record_script_url = f"{server_url}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records/{record_id}"
                script_data = {
                    "script": "PDFTimesheet",
                    "script.param": "/Users/Shared/ParkerPOsOCR/exports/test.pdf"
                }
                
                patch_response = requests.patch(record_script_url, json=script_data, headers=headers, verify=False, timeout=30)
                print(f"PATCH Status: {patch_response.status_code}")
                print(f"PATCH Response: {patch_response.text}")
                
                # Also try PUT
                put_response = requests.put(record_script_url, json=script_data, headers=headers, verify=False, timeout=30)
                print(f"PUT Status: {put_response.status_code}")
                print(f"PUT Response: {put_response.text}")
                
            else:
                print("No records found in layout")
        else:
            print(f"Failed to get records: {get_response.status_code}")
            
    except Exception as e:
        print(f"Error with record-based script: {str(e)}")

if __name__ == "__main__":
    test_script_execution_methods()

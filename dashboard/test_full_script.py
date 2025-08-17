#!/usr/bin/env python3
"""
Test FileMaker Script Execution
Test the actual PDF export script functionality
"""

import requests
import base64
import json
from datetime import datetime

def test_script_execution():
    """Test running the PDF export script on a record"""
    
    # Load configuration
    with open('filemaker_config.json', 'r') as f:
        config = json.load(f)
    
    server_url = f"https://{config['server']}:{config['port']}"
    database = config['database']
    username = config['username']
    password = config['password']
    
    print("=" * 60)
    print("FileMaker Script Execution Test")
    print("=" * 60)
    print(f"Server: {server_url}")
    print(f"Database: {database}")
    print(f"Time: {datetime.now()}")
    print()
    
    # Step 1: Authenticate
    print("1. Authenticating...")
    auth_url = f"{server_url}/fmi/data/v1/databases/{database}/sessions"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    try:
        auth_response = requests.post(auth_url, headers=headers, json={}, verify=False, timeout=10)
        if auth_response.status_code != 200:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            return
        
        auth_data = auth_response.json()
        token = auth_data['response']['token']
        print(f"   ✅ Authentication successful, token: {token[:20]}...")
        
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return
    
    # Step 2: Get some records to test with
    print("\n2. Getting test records...")
    headers['Authorization'] = f'Bearer {token}'
    
    try:
        records_url = f"{server_url}/fmi/data/v1/databases/{database}/layouts/Time Clock/records?_limit=5"
        records_response = requests.get(records_url, headers=headers, verify=False, timeout=10)
        
        if records_response.status_code != 200:
            print(f"   ❌ Failed to get records: {records_response.status_code}")
            return
        
        records_data = records_response.json()
        records = records_data['response']['data']
        
        if not records:
            print("   ⚠️  No records found in database")
            return
        
        print(f"   ✅ Found {len(records)} records")
        
        # Use first record for testing
        test_record = records[0]
        record_id = test_record['recordId']
        print(f"   📋 Testing with record ID: {record_id}")
        
    except Exception as e:
        print(f"   ❌ Error getting records: {e}")
        return
    
    # Step 3: Test script execution
    print("\n3. Testing script execution...")
    try:
        script_url = f"{server_url}/fmi/data/v1/databases/{database}/layouts/Time Clock/records/{record_id}"
        
        # Execute script without parameters (as configured)
        script_payload = {
            "fieldData": {},  # Required for PATCH requests
            "script": "PDF Export"
        }
        
        script_response = requests.patch(script_url, headers=headers, json=script_payload, verify=False, timeout=30)
        
        print(f"   📊 Response Status: {script_response.status_code}")
        
        if script_response.status_code == 200:
            script_data = script_response.json()
            script_error = script_data['response'].get('scriptError', 'Unknown')
            script_result = script_data['response'].get('scriptResult', '')
            
            print(f"   📝 Script Error Code: {script_error}")
            print(f"   📄 Script Result: {script_result}")
            
            if script_error == "0":
                print(f"   ✅ Script executed successfully!")
            else:
                print(f"   ⚠️  Script error code: {script_error}")
                
        else:
            print(f"   ❌ Script execution failed: {script_response.text}")
        
    except Exception as e:
        print(f"   ❌ Script execution error: {e}")
    
    # Step 4: Logout
    print("\n4. Logging out...")
    try:
        logout_url = f"{server_url}/fmi/data/v1/databases/{database}/sessions/{token}"
        logout_response = requests.delete(logout_url, headers=headers, verify=False, timeout=10)
        print(f"   ✅ Logout successful")
    except Exception as e:
        print(f"   ⚠️  Logout error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_script_execution()

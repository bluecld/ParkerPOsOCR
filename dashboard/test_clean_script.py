#!/usr/bin/env python3
"""
Test simplified FileMaker script that requires no parameters
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

def test_script_on_specific_record():
    """Test the PDFTimesheet script on a specific record"""
    print("🧪 === Testing PDFTimesheet Script on Specific Record ===\n")
    
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful\n")
    
    # Use a specific record ID and run script on that record
    record_id = "57704"  # Use a known record ID
    records_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records/{record_id}"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Run script on a specific record
    script_data = {
        "script": "PDFTimesheet",
        "fieldData": {}  # Empty field data since we're not updating anything
    }
    
    print(f"🚀 Executing PDFTimesheet script on record {record_id}...")
    print("📄 Script should automatically save PDF to server Documents folder")
    
    try:
        response = requests.patch(
            records_url,
            json=script_data,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            script_error = result.get('response', {}).get('scriptError', 'unknown')
            script_result = result.get('response', {}).get('scriptResult', 'no result')
            
            print(f"📋 Record ID: {record_id}")
            print(f"🔢 Script Error Code: {script_error}")
            print(f"📄 Script Result: {script_result}")
            
            if script_error == "0":
                print("\n🎉 SUCCESS! Script executed without errors!")
                if script_result and script_result != "no result":
                    print(f"✅ Script Result: {script_result}")
                else:
                    print("📁 PDF export completed (no specific result returned)")
                return True
            else:
                print(f"\n❌ Script Error {script_error}")
                print(f"📄 Error Details: {script_result}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_script_via_scripts_endpoint():
    """Test the PDFTimesheet script using the scripts endpoint"""
    print("🧪 === Testing PDFTimesheet Script via Scripts Endpoint ===\n")
    
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful\n")
    
    # Use the scripts endpoint
    script_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/scripts/PDFTimesheet"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # No script parameters
    script_data = {}
    
    print("🚀 Executing PDFTimesheet script via scripts endpoint...")
    print("📄 Script should automatically save PDF to server Documents folder")
    
    try:
        response = requests.post(
            script_url,
            json=script_data,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            script_error = result.get('response', {}).get('scriptError', 'unknown')
            script_result = result.get('response', {}).get('scriptResult', 'no result')
            
            print(f"🔢 Script Error Code: {script_error}")
            print(f"📄 Script Result: {script_result}")
            
            if script_error == "0":
                print("\n🎉 SUCCESS! Script executed without errors!")
                if script_result and script_result != "no result":
                    print(f"✅ Script Result: {script_result}")
                else:
                    print("📁 PDF export completed (no specific result returned)")
                return True
            else:
                print(f"\n❌ Script Error {script_error}")
                print(f"📄 Error Details: {script_result}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎯 Testing FileMaker PDF Export - Multiple Approaches")
    print("=" * 60)
    
    # Test 1: Script on specific record (PATCH method)
    print("\n🔬 TEST 1: Script on Specific Record")
    success1 = test_script_on_specific_record()
    
    # Test 2: Scripts endpoint (POST method)
    print("\n🔬 TEST 2: Scripts Endpoint")
    success2 = test_script_via_scripts_endpoint()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"✅ Record Script Test: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Scripts Endpoint Test: {'PASSED' if success2 else 'FAILED'}")
    
    if success1 or success2:
        print("\n🎉 At least one method worked!")
        print("💡 Your FileMaker script is correctly configured.")
        if success1:
            print("👍 Recommended: Use script on specific record method")
        else:
            print("👍 Recommended: Use scripts endpoint method")
    else:
        print("\n❌ Both tests failed")
        print("💡 Check FileMaker script configuration and server setup")
        
    print("=" * 60)

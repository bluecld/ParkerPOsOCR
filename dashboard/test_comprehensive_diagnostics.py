#!/usr/bin/env python3
"""
Comprehensive diagnostic test for FileMaker PDFTimesheet script
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

def run_diagnostic_tests():
    """Run comprehensive diagnostic tests"""
    print("🔍 === FileMaker PDFTimesheet Script Diagnostics ===\n")
    
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed - stopping tests")
        return
    
    print("✅ Authentication successful\n")
    
    records_url = f"https://{config['server']}:{config['port']}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Progressive test cases
    test_cases = [
        {
            "name": "1. No Script Parameter (Default Behavior)",
            "description": "Test script with no parameters - should use default path",
            "script_data": {
                "script": "PDFTimesheet",
                "fieldData": {}
            }
        },
        {
            "name": "2. Empty String Parameter",
            "description": "Test with empty string parameter",
            "script_data": {
                "script": "PDFTimesheet",
                "script.param": "",
                "fieldData": {}
            }
        },
        {
            "name": "3. Simple Temp Folder",
            "description": "Test with /tmp/ folder - should be writable",
            "script_data": {
                "script": "PDFTimesheet",
                "script.param": "/tmp/",
                "fieldData": {}
            }
        },
        {
            "name": "4. Users Shared Folder",
            "description": "Test with /Users/Shared/ - standard Mac shared location",
            "script_data": {
                "script": "PDFTimesheet",
                "script.param": "/Users/Shared/",
                "fieldData": {}
            }
        },
        {
            "name": "5. Full File Path",
            "description": "Test with complete file path including filename",
            "script_data": {
                "script": "PDFTimesheet",
                "script.param": "/Users/Shared/test_export.pdf",
                "fieldData": {}
            }
        },
        {
            "name": "6. Target Export Folder",
            "description": "Test with our target ParkerPOsOCR exports folder",
            "script_data": {
                "script": "PDFTimesheet",
                "script.param": "/Users/Shared/ParkerPOsOCR/exports/",
                "fieldData": {}
            }
        }
    ]
    
    successful_tests = []
    
    for test_case in test_cases:
        print(f"🧪 {test_case['name']}")
        print(f"   📋 {test_case['description']}")
        
        param = test_case['script_data'].get('script.param', 'None')
        print(f"   📂 Parameter: {param}")
        
        try:
            response = requests.post(
                records_url,
                json=test_case['script_data'],
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                script_error = result.get('response', {}).get('scriptError', 'unknown')
                script_result = result.get('response', {}).get('scriptResult', 'no result')
                
                if script_error == "0":
                    print(f"   ✅ SUCCESS!")
                    print(f"   📄 Result: {script_result}")
                    successful_tests.append(test_case['name'])
                    print("   🎯 This parameter format works!\n")
                else:
                    print(f"   ❌ Script Error: {script_error}")
                    print(f"   📄 Script Result: {script_result}")
                    
                    if script_error == "800":
                        print("   💡 Error 800 indicates file/folder access issue")
                    elif script_error == "802":
                        print("   💡 Error 802 indicates missing file/folder")
                    elif script_error == "10":
                        print("   💡 Error 10 indicates missing or invalid parameters")
                    
                    print()
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}\n")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}\n")
    
    # Summary
    print("📊 === DIAGNOSTIC SUMMARY ===")
    if successful_tests:
        print("✅ Successful test cases:")
        for test in successful_tests:
            print(f"   • {test}")
        print("\n🎉 Use the successful parameter format in your integration!")
    else:
        print("❌ No tests were successful")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Check FileMaker script syntax in FileMaker Pro")
        print("2. Test the script manually in FileMaker Pro first")
        print("3. Verify folder permissions on Mac server")
        print("4. Check if FileMaker Server has write access to target folders")
        print("5. Review the script's error handling logic")
    
    print("\n💻 NEXT ACTIONS:")
    print("1. Test the script manually in FileMaker Pro")
    print("2. Add debug statements to the FileMaker script")
    print("3. Check Mac server folder permissions via SSH")
    print("4. Verify FileMaker Server service permissions")

if __name__ == "__main__":
    run_diagnostic_tests()

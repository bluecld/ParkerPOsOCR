#!/usr/bin/env python3
"""
Test the#!/usr/bin/env python3
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

def test_simplified_script():
    """Test the PDFTimesheet script with no parameters"""
    print("🧪 === Testing Simplified PDFTimesheet Script ===\n")
    
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful
")
    
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
    
    print("🚀 Executing PDFTimesheet script with no parameters...")
    print("📄 Script should automatically save PDF to server Documents folder")
    
    try:
        response = requests.post(
            records_url,
            json=script_data,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"
📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            script_error = result.get('response', {}).get('scriptError', 'unknown')
            script_result = result.get('response', {}).get('scriptResult', 'no result')
            record_id = result.get('response', {}).get('recordId', 'unknown')
            
            print(f"📋 Record ID: {record_id}")
            print(f"🔢 Script Error Code: {script_error}")
            print(f"📄 Script Result: {script_result}")
            
            if script_error == "0":
                print("
🎉 SUCCESS! Script executed without errors!")
                print(f"✅ PDF Export Result: {script_result}")
                
                if "SUCCESS:" in str(script_result):
                    file_path = script_result.replace("SUCCESS:", "").strip()
                    print(f"📁 PDF saved to: {file_path}")
                elif script_result:
                    print(f"📁 PDF export completed: {script_result}")
                else:
                    print("📁 PDF export completed (no file path returned)")
                    
                return True
            else:
                print(f"
❌ Script Error {script_error}")
                print(f"📄 Error Details: {script_result}")
                
                if script_error == "800":
                    print("
💡 Error 800 Troubleshooting:")
                    print("   - Check FileMaker script uses Get(DocumentsPath)")
                    print("   - Verify 'Create directories: On' in Save Records as PDF")
                    print("   - Ensure proper file extension (.pdf)")
                    print("   - Check fmserver user permissions")
                elif script_error == "802":
                    print("
💡 Error 802: File or folder not found")
                elif script_error == "10":
                    print("
💡 Error 10: Invalid or missing parameter")
                
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_filemaker_integration():
    """Test the actual FileMaker integration class"""
    print("
🔧 === Testing FileMaker Integration Class ===
")
    
    try:
        import sys
        sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')
        from filemaker_integration import FileMakerIntegration
        
        # Create integration instance
        server_url = f"https://{config['server']}:{config['port']}"
        fm = FileMakerIntegration(
            server_url=server_url,
            database=config['database'],
            username=config['username'],
            password=config['password'],
            ssl_verify=config.get('ssl_verify', False),
            timeout=config.get('timeout', 30)
        )
        
        # Test authentication
        print("🔐 Testing authentication...")
        auth_success = fm.authenticate()
        
        if auth_success:
            print("✅ Authentication successful!")
            
            # Test PDF export
            print("📄 Testing PDF export...")
            result = fm.export_record_as_pdf("57704", config['layout'])  # Use a known record ID
            
            if result:
                print(f"✅ PDF export successful: {result}")
                return True
            else:
                print("❌ PDF export failed")
                return False
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 Testing FileMaker PDF Export with Simplified Script")
    print("=" * 60)
    
    # Test 1: Direct API call
    success1 = test_simplified_script()
    
    # Test 2: Integration class
    success2 = test_filemaker_integration()
    
    print("
" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"✅ Direct API Test: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Integration Test: {'PASSED' if success2 else 'FAILED'}")
    
    if success1 and success2:
        print("
🎉 ALL TESTS PASSED! PDF export is working!")
        print("💡 Your FileMaker script is correctly configured.")
    elif success1:
        print("
⚠️  API works but integration needs fixing")
    elif success2:
        print("
⚠️  Integration works but API call needs fixing")
    else:
        print("
❌ Both tests failed - check FileMaker script configuration")
        
    print("=" * 60)

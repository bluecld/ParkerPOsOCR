#!/usr/bin/env python3
"""
Test current FileMaker integration with correct authentication
"""

import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

from filemaker_integration import FileMakerIntegration
import json

def test_filemaker_integration():
    """Test the FileMaker integration with current config"""
    
    # Load config
    with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
        config = json.load(f)
    
    print("=== Testing FileMaker Integration Class ===")
    print(f"Server: {config['server']}:{config['port']}")
    print(f"Database: {config['database']}")
    print(f"Username: {config['username']}")
    print()
    
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
    
    # Test authentication
    print("1. Testing authentication...")
    auth_success = fm.authenticate()
    
    if auth_success:
        print(f"✅ Authentication successful! Token: {fm.token[:20]}...")
        print()
        
        # Test getting layout info
        print("2. Testing layout access...")
        try:
            layout_url = f"{server_url}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}"
            headers = fm.get_headers()
            
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(
                layout_url,
                headers=headers,
                verify=config.get('ssl_verify', False),
                timeout=config.get('timeout', 30)
            )
            
            print(f"Layout access status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("✅ Layout accessible!")
                print(f"Layout name: {result.get('response', {}).get('layout', 'Unknown')}")
            else:
                print(f"❌ Layout access failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Layout test error: {str(e)}")
        
        print()
        
        # Test PDF export script
        print("3. Testing PDFTimesheet script...")
        try:
            script_url = f"{server_url}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/script/PDFTimesheet"
            
            # Try with simple test parameters
            test_params = {
                "script": "PDFTimesheet",
                "script.param": "/Users/Shared/ParkerPOsOCR/exports/test_export.pdf"
            }
            
            response = requests.post(
                script_url,
                json=test_params,
                headers=headers,
                verify=config.get('ssl_verify', False),
                timeout=config.get('timeout', 30)
            )
            
            print(f"Script execution status: {response.status_code}")
            result = response.json()
            print(f"Script response: {json.dumps(result, indent=2)}")
            
            # Check for script error
            script_error = result.get('response', {}).get('scriptError', 'unknown')
            if script_error == "0":
                print("✅ Script executed successfully!")
            else:
                print(f"❌ Script error: {script_error}")
                if script_error == "800":
                    print("   Error 800 typically means file/folder permission or path issue")
                
        except Exception as e:
            print(f"❌ Script test error: {str(e)}")
            
    else:
        print("❌ Authentication failed!")
    
    print("\n=== Integration Test Complete ===")

if __name__ == "__main__":
    test_filemaker_integration()

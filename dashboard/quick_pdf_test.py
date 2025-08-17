#!/usr/bin/env python3
"""
Minimal test for PDFTimesheet script with debugging output
"""

import os
import sys
import json

sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def quick_pdf_test():
    try:
        from filemaker_integration import FileMakerIntegration
        
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        server_url = f"https://{config['server']}:{config['port']}"
        fm = FileMakerIntegration(
            server_url=server_url,
            database=config['database'],
            username=config['username'],
            password=config['password'],
            ssl_verify=False
        )
        
        print("🔐 Authenticating...")
        if not fm.authenticate():
            print("❌ Auth failed")
            return
        
        print("✅ Authenticated")
        
        # Just test PDFTimesheet with very simple parameter
        record_id = "57703"
        print(f"📝 Testing PDFTimesheet script on record {record_id}")
        
        # Create minimal test parameters
        simple_param = "test"
        
        print(f"Parameters: {simple_param}")
        
        # Use direct API call to test script
        script_url = f"{server_url}/fmi/data/v1/databases/{config['database']}/layouts/{config['layout']}/records/{record_id}"
        
        payload = {
            "fieldData": {},  
            "script": "PDFTimesheet",
            "script.param": simple_param
        }
        
        print("🚀 Making direct API call...")
        
        import requests
        response = requests.patch(
            script_url,
            json=payload,
            headers=fm.get_headers(),
            verify=False,
            timeout=10  # Short timeout
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result}")
            script_result = result.get('response', {}).get('scriptResult', '')
            script_error = result.get('response', {}).get('scriptError', '')
            print(f"Script result: '{script_result}'")
            print(f"Script error: '{script_error}'")
        else:
            print(f"Error: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== Quick PDFTimesheet Test ===")
    quick_pdf_test()
    print("=" * 35)

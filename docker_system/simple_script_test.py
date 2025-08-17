#!/usr/bin/env python3
"""
Simple test to call your existing FileMaker PDFTimesheet script
without overcomplicating the integration
"""

import requests
import json
import sys

def test_filemaker_script(po_number):
    """Just call your existing PDFTimesheet script"""
    server = 'https://192.168.0.105'
    database = 'PreInventory'
    
    # Login
    login_url = f'{server}/fmi/data/v1/databases/{database}/sessions'
    login_data = {
        'fmDataSource': [{
            'database': database, 
            'username': 'ParkerPOs', 
            'password': 'Inventoried'
        }]
    }
    
    try:
        print(f"🔄 Connecting to FileMaker Server...")
        response = requests.post(login_url, json=login_data, verify=False)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        token = response.json().get('response', {}).get('token')
        print(f"✅ Connected successfully")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Call your PDFTimesheet script directly
        print(f"🔄 Calling PDFTimesheet script with PO: {po_number}")
        
        script_url = f'{server}/fmi/data/v1/databases/{database}/layouts/Time Clock/script/PDFTimesheet'
        script_data = {
            'script.param': po_number
        }
        
        script_response = requests.post(script_url, json=script_data, headers=headers, verify=False)
        
        print(f"📊 Script Response Status: {script_response.status_code}")
        
        if script_response.status_code == 200:
            result = script_response.json()
            script_error = result.get('response', {}).get('scriptError', 'Unknown')
            script_result = result.get('response', {}).get('scriptResult', 'No result')
            
            print(f"✅ Script executed")
            print(f"   Error Code: {script_error}")
            print(f"   Script Result: {script_result}")
            
            if script_error == '0':
                print(f"📄 PDF should be at: filemac:/Macintosh HD/Users/Shared/ParkerPOsOCR/exports/{po_number}.pdf")
            else:
                print(f"⚠️ Script error occurred: {script_error}")
        else:
            print(f"❌ Script call failed: {script_response.text}")
        
        # Logout
        logout_url = f'{server}/fmi/data/v1/databases/{database}/sessions/{token}'
        requests.delete(logout_url, verify=False)
        print(f"✅ Session closed")
        
        return script_response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    po_number = sys.argv[1] if len(sys.argv) > 1 else "DIRECTTEST123"
    test_filemaker_script(po_number)

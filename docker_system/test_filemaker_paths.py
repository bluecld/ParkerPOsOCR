#!/usr/bin/env python3
"""
Test script to help debug FileMaker PDF path issues
"""

import requests
import json
import os

def test_filemaker_paths():
    """Test different path configurations for FileMaker PDF generation"""
    
    server = 'https://192.168.0.105:443'
    database = 'PreInventory'
    username = 'JSON'
    password = 'Windu63Purple!'
    
    print('🔍 FileMaker Path Testing Utility')
    print('='*50)
    
    # Authentication
    auth_url = f'{server}/fmi/data/v1/databases/{database}/sessions'
    auth_data = json.dumps({
        'fmDataSource': [
            {
                'database': database,
                'username': username,
                'password': password
            }
        ]
    })
    
    try:
        auth_response = requests.post(auth_url, data=auth_data, headers={'Content-Type': 'application/json'}, verify=False)
        
        if auth_response.status_code == 200:
            token = auth_response.json().get('response', {}).get('token')
            print('✅ FileMaker authentication successful')
            
            print('\n📋 RECOMMENDATIONS FOR YOUR FILEMAKER SCRIPT:')
            print('-' * 50)
            
            print('\n1. 🧪 TEST PATH (Desktop - should work):')
            print('   Set Variable [$path; Value: "/Users/parker/Desktop/" & $po & ".pdf"]')
            print('   Or: Set Variable [$path; Value: "file:/Users/parker/Desktop/" & $po & ".pdf"]')
            
            print('\n2. 🎯 TARGET PATH (Shared folder):')
            print('   Set Variable [$path; Value: "/Users/Shared/ParkerPOsOCR/exports/" & $po & ".pdf"]')
            print('   Or: Set Variable [$path; Value: "file:/Users/Shared/ParkerPOsOCR/exports/" & $po & ".pdf"]')
            
            print('\n3. 🔧 ALTERNATIVE PATHS TO TRY:')
            print('   • "/tmp/" & $po & ".pdf"  (Temporary directory - for testing)')
            print('   • "/Users/Shared/" & $po & ".pdf"  (Basic shared folder)')
            print('   • "~/Desktop/" & $po & ".pdf"  (User desktop)')
            
            print('\n4. 📁 DIRECTORY CREATION:')
            print('   Before running your script, manually create this directory on your Mac:')
            print('   mkdir -p /Users/Shared/ParkerPOsOCR/exports')
            print('   chmod 755 /Users/Shared/ParkerPOsOCR/exports')
            
            print('\n5. 🔍 DEBUGGING STEPS:')
            print('   a) Add this to your script BEFORE "Save Records as PDF":')
            print('      Show Custom Dialog [Title: "Debug Path"; Message: $path]')
            print('   b) Try saving to Desktop first to confirm script works')
            print('   c) Check FileMaker Server logs for permission errors')
            
            print('\n6. ⚠️  COMMON ISSUES:')
            print('   • Directory /Users/Shared/ParkerPOsOCR/exports/ might not exist')
            print('   • FileMaker Server might not have write permissions')
            print('   • Path syntax might need "file:" prefix')
            print('   • Spaces in paths might need URL encoding (%20)')
            
            # Test with a simple path creation
            test_po = 'PATHTEST123'
            
            print(f'\n🧪 TESTING WITH PO: {test_po}')
            
            # Create a PreInventory record and test the script
            preinventory_url = f"{server}/fmi/data/v1/databases/{database}/layouts/PreInventory/records"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            test_data = {
                "fieldData": {
                    "IncomingPO": test_po,
                    "Part Number": "TESTPART",
                    "QTY": 1
                },
                "script": "PDFTimesheet",
                "script.param": test_po
            }
            
            response = requests.post(preinventory_url, json=test_data, headers=headers, verify=False)
            
            if response.status_code == 200:
                result = response.json().get('response', {})
                script_error = result.get('scriptError', 'Unknown')
                script_result = result.get('scriptResult', 'No result')
                record_id = result.get('recordId', 'Unknown')
                
                print(f'✅ Test record created: {record_id}')
                print(f'📄 Script error code: {script_error}')
                print(f'📄 Script result: {script_result}')
                
                if script_error == '0':
                    print('✅ Script executed successfully!')
                    print('💡 Now check these locations on your Mac:')
                    print('   • /Users/Shared/ParkerPOsOCR/exports/PATHTEST123.pdf')
                    print('   • /Users/parker/Desktop/PATHTEST123.pdf')
                    print('   • /tmp/PATHTEST123.pdf')
                else:
                    print(f'⚠️ Script error {script_error} - check FileMaker script steps')
            else:
                print(f'❌ Test failed: {response.status_code} - {response.text}')
            
            # Cleanup
            requests.delete(f'{server}/fmi/data/v1/databases/{database}/sessions/{token}', verify=False)
            
        else:
            print(f'❌ Authentication failed: {auth_response.status_code}')
            print(f'Response: {auth_response.text}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_filemaker_paths()

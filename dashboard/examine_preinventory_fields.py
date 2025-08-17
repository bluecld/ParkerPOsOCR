#!/usr/bin/env python3

import json
import sys
import os
import requests
import base64

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def get_preinventory_fields():
    """Get all fields available in the PreInventory layout to see what's available"""
    try:
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Examining PreInventory Layout Fields ===")
        
        protocol = "https" if config['port'] == 443 else "http"
        server_url = f"{protocol}://{config['server']}:{config['port']}"
        
        # Authenticate to PreInventory database
        auth_url = f"{server_url}/fmi/data/v1/databases/PreInventory/sessions"
        
        credentials = base64.b64encode(f"{config['username']}:{config['password']}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        auth_response = requests.post(
            auth_url, 
            headers=headers, 
            json={}, 
            verify=config.get('ssl_verify', False), 
            timeout=config.get('timeout', 30)
        )
        
        if auth_response.status_code != 200:
            print("❌ Authentication failed")
            return
            
        auth_result = auth_response.json()
        token = auth_result.get('response', {}).get('token')
        
        if not token:
            print("❌ No token received")
            return
            
        print("✅ Authentication successful")
        
        api_headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get all records from PreInventory layout (limit to 1 to see structure)
        records_url = f"{server_url}/fmi/data/v1/databases/PreInventory/layouts/PreInventory/records"
        
        params = {
            "_limit": 1
        }
        
        records_response = requests.get(
            records_url, 
            params=params,
            headers=api_headers, 
            verify=config.get('ssl_verify', False), 
            timeout=config.get('timeout', 30)
        )
        
        if records_response.status_code == 200:
            records_result = records_response.json()
            records = records_result.get('response', {}).get('data', [])
            
            if records:
                sample_record = records[0]
                field_data = sample_record.get('fieldData', {})
                
                print(f"\n📋 Fields available in PreInventory layout:")
                print(f"Found {len(field_data)} fields:")
                
                for field_name, field_value in field_data.items():
                    print(f"   {field_name}: {field_value}")
                
                print(f"\n🔍 Looking for lookup-related fields:")
                lookup_fields = []
                for field_name in field_data.keys():
                    if any(word in field_name.upper() for word in ['PART', 'DESC', 'REV', 'SHEET', 'OP', 'PRICE']):
                        lookup_fields.append(field_name)
                        print(f"   ✅ {field_name}")
                
                if lookup_fields:
                    print(f"\n💡 Based on the current FileMaker setup:")
                    print(f"   - The PreInventory layout has these fields: {lookup_fields}")
                    print(f"   - The Description, Revision, Op Sheet Issue fields should get values from lookups")
                    print(f"   - Since PRICES data is in a separate database, these are probably lookup fields")
                    print(f"   - The API approach won't work because we need access to the PRICES database")
                    
                    print(f"\n🎯 Recommendation:")
                    print(f"   Since the PRICES database is separate and we don't have access:")
                    print(f"   1. Use FileMaker relationships and lookups (traditional approach)")
                    print(f"   2. Create a FileMaker script that handles the lookups internally")
                    print(f"   3. Or get access credentials for the PRICES 7-9-2002 database")
                else:
                    print(f"\n⚠️ No obvious lookup fields found in PreInventory layout")
            else:
                print(f"❌ No records found in PreInventory layout")
        else:
            print(f"❌ Failed to get records: {records_response.status_code} - {records_response.text}")
        
        # Let's also try to create a simple test record to see what happens
        print(f"\n🧪 Testing record creation to see field behavior:")
        
        create_url = f"{server_url}/fmi/data/v1/databases/PreInventory/layouts/PreInventory/records"
        
        test_payload = {
            "fieldData": {
                "Whittaker Shipper #": "TEST123",
                "PART NUMBER": "450130*OP40",
                "QTY SHIP": "1",
                "MJO NO": "TEST",
                "Promise Delivery Date": "08/14/2025",
                "Planner Name": "Nora Seclen"
            }
        }
        
        create_response = requests.post(
            create_url, 
            json=test_payload, 
            headers=api_headers, 
            verify=config.get('ssl_verify', False), 
            timeout=config.get('timeout', 30)
        )
        
        if create_response.status_code in [200, 201]:
            create_result = create_response.json()
            record_id = create_result.get('response', {}).get('recordId')
            
            print(f"✅ Test record created with ID: {record_id}")
            
            # Get the record back to see if lookups happened automatically
            get_url = f"{server_url}/fmi/data/v1/databases/PreInventory/layouts/PreInventory/records/{record_id}"
            
            get_response = requests.get(
                get_url, 
                headers=api_headers, 
                verify=config.get('ssl_verify', False), 
                timeout=config.get('timeout', 30)
            )
            
            if get_response.status_code == 200:
                get_result = get_response.json()
                record_data = get_result.get('response', {}).get('data', [{}])[0]
                final_fields = record_data.get('fieldData', {})
                
                print(f"\n📋 Test record after creation:")
                for field_name, field_value in final_fields.items():
                    if any(word in field_name.upper() for word in ['PART', 'DESC', 'REV', 'SHEET', 'OP']):
                        print(f"   {field_name}: {field_value}")
                
                # Check if lookups worked
                desc = final_fields.get('Description', '')
                rev = final_fields.get('Revision', '')
                op_sheet = final_fields.get('Op Sheet Issue', '')
                
                if desc or rev or op_sheet:
                    print(f"\n🎉 SUCCESS: Lookups worked automatically!")
                    print(f"   FileMaker's internal relationship/lookup mechanism is working")
                    print(f"   No API simulation needed!")
                else:
                    print(f"\n❌ Lookups did not populate automatically")
                    print(f"   This confirms that manual lookup simulation is needed")
                    print(f"   OR access to the PRICES database is required")
            
            # Clean up - delete the test record
            delete_response = requests.delete(
                get_url, 
                headers=api_headers, 
                verify=config.get('ssl_verify', False), 
                timeout=config.get('timeout', 30)
            )
            
            if delete_response.status_code == 200:
                print(f"🗑️ Test record deleted successfully")
            
        else:
            print(f"❌ Failed to create test record: {create_response.status_code} - {create_response.text}")
        
        # Logout
        logout_url = f"{server_url}/fmi/data/v1/databases/PreInventory/sessions/{token}"
        requests.delete(logout_url, headers=api_headers, verify=config.get('ssl_verify', False), timeout=config.get('timeout', 30))
        
    except Exception as e:
        print(f"❌ Error examining PreInventory fields: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_preinventory_fields()

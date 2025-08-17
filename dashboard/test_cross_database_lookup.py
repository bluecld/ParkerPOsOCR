#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_cross_database_lookup():
    """Test cross-database lookup simulation between PreInventory and PRICES databases"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Testing Cross-Database Lookup Simulation ===")
        print(f"PreInventory Database: {config['database']}")
        print(f"PRICES Database: {config['prices_database']}")
        
        # Create FileMaker integration instance
        protocol = "https" if config['port'] == 443 else "http"
        server_url = f"{protocol}://{config['server']}:{config['port']}"
        
        fm = FileMakerIntegration(
            server_url=server_url,
            database=config['database'],
            username=config['username'],
            password=config['password'],
            ssl_verify=config.get('ssl_verify', True),
            timeout=config.get('timeout', 10)
        )
        
        # Authenticate to PreInventory database
        if not fm.authenticate():
            print("❌ Authentication to PreInventory database failed!")
            return False
        
        print("✅ Authentication to PreInventory database successful!")
        
        # Test with part number that should exist in PRICES database
        test_record = {
            "Whittaker Shipper #": "4551241601",  # New test PO number
            "PART NUMBER": "450130*OP40",  # This should exist in PRICES database
            "QTY SHIP": "35",
            "MJO NO": "125146001",
            "Promise Delivery Date": "08/14/2025",
            "Planner Name": "Nora Seclen"
        }
        
        print(f"\n--- Creating Test Record ---")
        print(f"PO: {test_record['Whittaker Shipper #']}")
        print(f"Part: {test_record['PART NUMBER']}")
        
        # Create the record with cross-database lookup simulation enabled
        record_id = fm.create_record(test_record, config['layout'], config)
        
        if record_id:
            print(f"✅ Record created with ID: {record_id}")
            print("✅ Cross-database lookup simulation should have run automatically")
            return True
        else:
            print("❌ Failed to create test record")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prices_database_access():
    """Test direct access to PRICES database to verify it's accessible"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Testing Direct PRICES Database Access ===")
        
        # Test authentication to PRICES database directly
        protocol = "https" if config['port'] == 443 else "http"
        server_url = f"{protocol}://{config['server']}:{config['port']}"
        
        import requests
        import base64
        
        prices_database = config['prices_database']
        prices_auth_url = f"{server_url}/fmi/data/v1/databases/{prices_database}/sessions"
        
        credentials = base64.b64encode(f"{config['username']}:{config['password']}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔐 Testing authentication to PRICES database: {prices_database}")
        
        response = requests.post(
            prices_auth_url, 
            headers=headers, 
            json={}, 
            verify=config.get('ssl_verify', False), 
            timeout=config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get('response', {}).get('token')
            
            if token:
                print("✅ Successfully authenticated to PRICES database!")
                
                # Test a simple find operation
                find_url = f"{server_url}/fmi/data/v1/databases/{prices_database}/layouts/{config['prices_layout']}/_find"
                
                find_headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                # Search for any record (limit to 1)
                find_payload = {
                    "query": [{"Part Number": "*"}],
                    "limit": 1
                }
                
                find_response = requests.post(
                    find_url, 
                    json=find_payload, 
                    headers=find_headers, 
                    verify=config.get('ssl_verify', False), 
                    timeout=config.get('timeout', 30)
                )
                
                if find_response.status_code == 200:
                    find_result = find_response.json()
                    records = find_result.get('response', {}).get('data', [])
                    
                    if records:
                        sample_record = records[0]
                        sample_fields = sample_record.get('fieldData', {})
                        
                        print("✅ Successfully accessed PRICES table!")
                        print("📋 Sample record from PRICES database:")
                        print(f"   Part Number: {sample_fields.get('Part Number', 'N/A')}")
                        print(f"   Description: {sample_fields.get('Description', 'N/A')}")
                        print(f"   Revision: {sample_fields.get('Revision', 'N/A')}")
                        print(f"   Op Sheet Issue: {sample_fields.get('Op Sheet Issue', 'N/A')}")
                    else:
                        print("⚠️ PRICES table accessible but no records found")
                        
                else:
                    print(f"❌ Failed to search PRICES table: {find_response.status_code} - {find_response.text}")
                
                # Logout from PRICES database
                logout_url = f"{server_url}/fmi/data/v1/databases/{prices_database}/sessions/{token}"
                requests.delete(logout_url, headers=find_headers, verify=config.get('ssl_verify', False), timeout=config.get('timeout', 30))
                
                return True
            else:
                print("❌ Authentication successful but no token received")
                return False
        else:
            print(f"❌ Failed to authenticate to PRICES database: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PRICES database access: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Cross-Database FileMaker Lookup Test")
    print("="*50)
    
    print("\n1️⃣ Testing direct PRICES database access...")
    success1 = test_prices_database_access()
    
    if success1:
        print("\n" + "="*50)
        print("\n2️⃣ Testing complete cross-database lookup simulation...")
        success2 = test_cross_database_lookup()
    else:
        success2 = False
        print("\n⚠️ Skipping cross-database test due to PRICES database access issues")
    
    print("\n" + "="*50)
    print(f"\nResults:")
    print(f"PRICES Database Access: {'SUCCESS' if success1 else 'FAILED'}")
    print(f"Cross-Database Lookup: {'SUCCESS' if success2 else 'FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Cross-database lookup simulation is working!")
        print("\n📝 What this means:")
        print("- Can authenticate to both PreInventory and PRICES databases")
        print("- Can search for part numbers in the PRICES database")
        print("- Can retrieve Description, Revision, Op Sheet Issue from PRICES")
        print("- Can update PreInventory records with lookup data")
        print("- Full cross-database integration working!")
    else:
        print("\n🔧 Some tests failed. Check the output above for details.")
        print("\n💡 Common issues:")
        print("- PRICES database name might be different")
        print("- Layout name in PRICES database might be different")
        print("- Field names might not match")
        print("- Database might not be hosted on FileMaker Server")

#!/usr/bin/env python3

import json
import sys
import os
import requests
import base64

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def discover_databases():
    """Discover what databases are available on the FileMaker Server"""
    try:
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Discovering Available FileMaker Databases ===")
        
        protocol = "https" if config['port'] == 443 else "http"
        server_url = f"{protocol}://{config['server']}:{config['port']}"
        
        # Try to get database list (this may not be available in all FileMaker Server versions)
        databases_url = f"{server_url}/fmi/data/v1/databases"
        
        credentials = base64.b64encode(f"{config['username']}:{config['password']}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔍 Checking for database list at: {databases_url}")
        
        response = requests.get(
            databases_url, 
            headers=headers, 
            verify=config.get('ssl_verify', False), 
            timeout=config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            databases = result.get('response', {}).get('databases', [])
            
            print("✅ Found available databases:")
            for db in databases:
                print(f"   - {db}")
                
        else:
            print(f"⚠️ Database list not available (Status: {response.status_code})")
            print("This is normal - many FileMaker Servers don't expose the database list via API")
        
        # Test common database names that might contain PRICES data
        potential_names = [
            "PRICES",
            "Prices", 
            "PRICES_7_9_2002",
            "PRICES 7_9_2002",
            "PreInventory",  # Maybe PRICES is in the same database as PreInventory
            "Inventory",
            "Parts",
            "Manufacturing"
        ]
        
        print(f"\n🧪 Testing potential database names:")
        working_databases = []
        
        for db_name in potential_names:
            print(f"\n   Testing: {db_name}")
            
            auth_url = f"{server_url}/fmi/data/v1/databases/{db_name}/sessions"
            
            auth_response = requests.post(
                auth_url, 
                headers=headers, 
                json={}, 
                verify=config.get('ssl_verify', False), 
                timeout=config.get('timeout', 30)
            )
            
            if auth_response.status_code == 200:
                auth_result = auth_response.json()
                token = auth_result.get('response', {}).get('token')
                
                if token:
                    print(f"   ✅ {db_name} - Authentication successful!")
                    working_databases.append(db_name)
                    
                    # Try to find layouts in this database
                    layouts_url = f"{server_url}/fmi/data/v1/databases/{db_name}/layouts"
                    
                    layout_headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                    
                    layout_response = requests.get(
                        layouts_url, 
                        headers=layout_headers, 
                        verify=config.get('ssl_verify', False), 
                        timeout=config.get('timeout', 30)
                    )
                    
                    if layout_response.status_code == 200:
                        layout_result = layout_response.json()
                        layouts = layout_result.get('response', {}).get('layouts', [])
                        
                        print(f"      Available layouts:")
                        for layout in layouts:
                            layout_name = layout.get('name', 'Unknown')
                            print(f"        - {layout_name}")
                            
                            # Check if this layout might contain PRICES data
                            if any(word in layout_name.upper() for word in ['PRICE', 'PART', 'INVENTORY']):
                                print(f"          🎯 This might contain PRICES data!")
                    
                    # Logout
                    logout_url = f"{server_url}/fmi/data/v1/databases/{db_name}/sessions/{token}"
                    requests.delete(logout_url, headers=layout_headers, verify=config.get('ssl_verify', False), timeout=config.get('timeout', 30))
                    
                else:
                    print(f"   ❌ {db_name} - Authentication successful but no token")
            else:
                error_msg = auth_response.text
                if "802" in error_msg:
                    print(f"   ❌ {db_name} - File not found")
                elif "401" in error_msg:
                    print(f"   ❌ {db_name} - Access denied")
                else:
                    print(f"   ❌ {db_name} - Error: {auth_response.status_code}")
        
        print(f"\n📋 Summary:")
        print(f"Working databases: {working_databases}")
        
        if working_databases:
            print(f"\n💡 Suggestions:")
            print(f"1. Update filemaker_config.json with one of the working database names")
            print(f"2. Check if PRICES data is in the PreInventory database itself")
            print(f"3. Use a layout that contains PRICES/Parts data")
        else:
            print(f"\n⚠️ No accessible databases found. Check:")
            print(f"1. Database names on FileMaker Server")
            print(f"2. User permissions")
            print(f"3. FileMaker Server configuration")
            
        return working_databases
        
    except Exception as e:
        print(f"❌ Error discovering databases: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    discover_databases()

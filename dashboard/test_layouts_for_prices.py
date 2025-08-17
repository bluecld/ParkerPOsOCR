#!/usr/bin/env python3

import json
import sys
import os
import requests
import base64

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_layouts_for_prices_data():
    """Test different layouts to find where PRICES data might be stored"""
    try:
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Testing Layouts for PRICES Data ===")
        
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
        
        # Get all layouts
        layouts_url = f"{server_url}/fmi/data/v1/databases/PreInventory/layouts"
        
        layout_response = requests.get(
            layouts_url, 
            headers=api_headers, 
            verify=config.get('ssl_verify', False), 
            timeout=config.get('timeout', 30)
        )
        
        if layout_response.status_code == 200:
            layout_result = layout_response.json()
            layouts = layout_result.get('response', {}).get('layouts', [])
            
            print(f"\n🔍 Testing {len(layouts)} layouts for Part Number field:")
            
            working_layouts = []
            
            for layout in layouts:
                layout_name = layout.get('name', 'Unknown')
                print(f"\n📋 Testing layout: {layout_name}")
                
                # Try to search for any record with a Part Number field
                find_url = f"{server_url}/fmi/data/v1/databases/PreInventory/layouts/{layout_name}/_find"
                
                # Test different possible field names for Part Number
                field_variations = [
                    "Part Number",
                    "PART NUMBER", 
                    "PartNumber",
                    "Part_Number",
                    "part_number"
                ]
                
                for field_name in field_variations:
                    try:
                        find_payload = {
                            "query": [{field_name: "*"}],
                            "limit": 1
                        }
                        
                        find_response = requests.post(
                            find_url, 
                            json=find_payload, 
                            headers=api_headers, 
                            verify=config.get('ssl_verify', False), 
                            timeout=config.get('timeout', 30)
                        )
                        
                        if find_response.status_code == 200:
                            find_result = find_response.json()
                            records = find_result.get('response', {}).get('data', [])
                            
                            if records:
                                sample_record = records[0]
                                sample_fields = sample_record.get('fieldData', {})
                                
                                print(f"   ✅ Found Part Number field: '{field_name}'")
                                print(f"   📝 Sample data:")
                                
                                # Show all fields that might be lookup-related
                                for key, value in sample_fields.items():
                                    if any(word in key.upper() for word in ['PART', 'DESC', 'REV', 'SHEET', 'OP', 'PRICE']):
                                        print(f"      {key}: {value}")
                                
                                working_layouts.append({
                                    'layout': layout_name,
                                    'part_field': field_name,
                                    'sample_fields': sample_fields
                                })
                                break  # Found working field, move to next layout
                                
                    except Exception as e:
                        # Continue to next field variation
                        continue
                
                if not any(wl['layout'] == layout_name for wl in working_layouts):
                    print(f"   ❌ No Part Number field found in {layout_name}")
            
            print(f"\n📋 Summary - Layouts with Part Number data:")
            for wl in working_layouts:
                print(f"   - {wl['layout']} (field: '{wl['part_field']}')")
                
                # Check if this layout has Description, Revision, Op Sheet Issue
                has_desc = any('desc' in key.lower() for key in wl['sample_fields'].keys())
                has_rev = any('rev' in key.lower() for key in wl['sample_fields'].keys())
                has_op = any('op' in key.lower() or 'sheet' in key.lower() for key in wl['sample_fields'].keys())
                
                if has_desc and has_rev and has_op:
                    print(f"     🎯 This layout has lookup fields! Use this for PRICES data.")
                elif has_desc or has_rev or has_op:
                    print(f"     ⚠️ This layout has some lookup fields")
                else:
                    print(f"     ❌ This layout doesn't have lookup fields")
            
            # Test specific part number
            if working_layouts:
                print(f"\n🧪 Testing specific Part Number: 450130*OP40")
                
                for wl in working_layouts:
                    layout_name = wl['layout']
                    part_field = wl['part_field']
                    
                    find_url = f"{server_url}/fmi/data/v1/databases/PreInventory/layouts/{layout_name}/_find"
                    
                    find_payload = {
                        "query": [{part_field: "450130*OP40"}]
                    }
                    
                    find_response = requests.post(
                        find_url, 
                        json=find_payload, 
                        headers=api_headers, 
                        verify=config.get('ssl_verify', False), 
                        timeout=config.get('timeout', 30)
                    )
                    
                    if find_response.status_code == 200:
                        find_result = find_response.json()
                        records = find_result.get('response', {}).get('data', [])
                        
                        if records:
                            print(f"\n✅ Found 450130*OP40 in layout: {layout_name}")
                            sample_record = records[0]
                            sample_fields = sample_record.get('fieldData', {})
                            
                            for key, value in sample_fields.items():
                                print(f"   {key}: {value}")
                        else:
                            print(f"❌ Part 450130*OP40 not found in {layout_name}")
                    else:
                        print(f"❌ Search failed in {layout_name}")
        
        # Logout
        logout_url = f"{server_url}/fmi/data/v1/databases/PreInventory/sessions/{token}"
        requests.delete(logout_url, headers=api_headers, verify=config.get('ssl_verify', False), timeout=config.get('timeout', 30))
        
    except Exception as e:
        print(f"❌ Error testing layouts: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_layouts_for_prices_data()

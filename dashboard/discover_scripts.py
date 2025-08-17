#!/usr/bin/env python3
"""
List Available FileMaker Scripts
Discover what scripts are available in the database
"""

import requests
import base64
import json
from datetime import datetime

def list_scripts():
    """List all available scripts in the FileMaker database"""
    
    # Load configuration
    with open('filemaker_config.json', 'r') as f:
        config = json.load(f)
    
    server_url = f"https://{config['server']}:{config['port']}"
    database = config['database']
    username = config['username']
    password = config['password']
    
    print("=" * 60)
    print("FileMaker Database Scripts Discovery")
    print("=" * 60)
    print(f"Server: {server_url}")
    print(f"Database: {database}")
    print()
    
    # Step 1: Authenticate
    print("1. Authenticating...")
    auth_url = f"{server_url}/fmi/data/v1/databases/{database}/sessions"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    try:
        auth_response = requests.post(auth_url, headers=headers, json={}, verify=False, timeout=10)
        if auth_response.status_code != 200:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            return
        
        auth_data = auth_response.json()
        token = auth_data['response']['token']
        print(f"   ✅ Authentication successful")
        
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return
    
    # Step 2: Get layout metadata to see scripts
    print("\n2. Getting database metadata...")
    headers['Authorization'] = f'Bearer {token}'
    
    try:
        # Get layout metadata
        metadata_url = f"{server_url}/fmi/data/v1/databases/{database}/layouts/Time Clock"
        metadata_response = requests.get(metadata_url, headers=headers, verify=False, timeout=10)
        
        if metadata_response.status_code == 200:
            metadata = metadata_response.json()
            print(f"   ✅ Layout metadata retrieved")
            
            # Print available information
            response_data = metadata.get('response', {})
            
            # Check for scripts information
            if 'scripts' in response_data:
                scripts = response_data['scripts']
                print(f"\n📋 Available Scripts ({len(scripts)}):")
                for i, script in enumerate(scripts, 1):
                    print(f"   {i}. {script}")
            else:
                print("   ⚠️  No scripts information in metadata")
                
        else:
            print(f"   ❌ Failed to get metadata: {metadata_response.status_code}")
            print(f"   Response: {metadata_response.text}")
    
    except Exception as e:
        print(f"   ❌ Error getting metadata: {e}")
    
    # Step 3: Try to get database-level information
    print("\n3. Getting database information...")
    try:
        db_info_url = f"{server_url}/fmi/data/v1/databases/{database}"
        db_response = requests.get(db_info_url, headers=headers, verify=False, timeout=10)
        
        if db_response.status_code == 200:
            db_data = db_response.json()
            print(f"   ✅ Database info retrieved")
            
            # Print database details
            response_data = db_data.get('response', {})
            
            if 'database' in response_data:
                db_info = response_data['database']
                print(f"   📊 Database: {db_info}")
                
        else:
            print(f"   ❌ Failed to get database info: {db_response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error getting database info: {e}")
    
    # Step 4: List layouts (which might give us more info)
    print("\n4. Getting available layouts...")
    try:
        layouts_url = f"{server_url}/fmi/data/v1/databases/{database}/layouts"
        layouts_response = requests.get(layouts_url, headers=headers, verify=False, timeout=10)
        
        if layouts_response.status_code == 200:
            layouts_data = layouts_response.json()
            layouts = layouts_data['response']['layouts']
            
            print(f"   ✅ Found {len(layouts)} layouts:")
            for layout in layouts:
                print(f"      - {layout['name']}")
                
        else:
            print(f"   ❌ Failed to get layouts: {layouts_response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error getting layouts: {e}")
    
    # Step 5: Logout
    print("\n5. Logging out...")
    try:
        logout_url = f"{server_url}/fmi/data/v1/databases/{database}/sessions/{token}"
        logout_response = requests.delete(logout_url, headers=headers, verify=False, timeout=10)
        print(f"   ✅ Logout successful")
    except Exception as e:
        print(f"   ⚠️  Logout error: {e}")
    
    print("\n" + "=" * 60)
    print("💡 Suggestion: Check the FileMaker database for script names")
    print("   Scripts need to be accessible via Data API")
    print("=" * 60)

if __name__ == "__main__":
    list_scripts()

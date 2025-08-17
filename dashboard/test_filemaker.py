#!/usr/bin/env python3

import requests
import json
import base64

# Configuration
server = "192.168.0.108"
port = 443
database = "PreInventory"
username = "JSON"
password = "Windu63Purple!"
layout = "PreInventory"

# Create credentials
credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
server_url = f"https://{server}:{port}"

print(f"Testing FileMaker Data API connection to {server_url}")
print(f"Database: {database}")
print(f"Layout: {layout}")
print(f"Username: {username}")
print("-" * 50)

# Test authentication
print("1. Testing authentication...")
auth_url = f"{server_url}/fmi/data/v1/databases/{database}/sessions"
headers = {
    'Authorization': f'Basic {credentials}',
    'Content-Type': 'application/json'
}

try:
    response = requests.post(auth_url, headers=headers, json={}, verify=False, timeout=10)
    print(f"Auth Response Status: {response.status_code}")
    print(f"Auth Response Body: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        token = result.get('response', {}).get('token')
        print(f"Token received: {token[:20]}..." if token else "No token in response")
        
        if token:
            # Test record creation
            print("\n2. Testing record creation...")
            create_url = f"{server_url}/fmi/data/v1/databases/{database}/layouts/{layout}/records"
            create_headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            test_data = {
                "fieldData": {
                    "Whittaker Shipper #": "TEST123"
                }
            }
            
            create_response = requests.post(create_url, headers=create_headers, json=test_data, verify=False, timeout=10)
            print(f"Create Response Status: {create_response.status_code}")
            print(f"Create Response Body: {create_response.text}")
    else:
        print("Authentication failed!")
        
except Exception as e:
    print(f"Error: {e}")

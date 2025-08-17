#!/usr/bin/env python3
"""
Test FileMaker Server Connection
Quick diagnostic tool for FileMaker connectivity issues
"""

import requests
import base64
import json
import socket
from datetime import datetime

def test_network_connectivity(host, port, timeout=3):
    """Test basic network connectivity"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_filemaker_auth(server_url, database, username, password, timeout=10):
    """Test FileMaker Data API authentication"""
    try:
        auth_url = f"{server_url}/fmi/data/v1/databases/{database}/sessions"
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            auth_url, 
            headers=headers, 
            json={}, 
            verify=False, 
            timeout=timeout
        )
        
        return {
            'success': response.status_code in [200, 201],
            'status_code': response.status_code,
            'response': response.text[:200]
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"{type(e).__name__}: {str(e)}"
        }

def main():
    print("=" * 60)
    print("FileMaker Server Connection Test")
    print("=" * 60)
    
    # Load configuration
    try:
        with open('filemaker_config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    server = config['server']
    port = config['port']
    database = config['database']
    username = config['username']
    password = config['password']
    
    server_url = f"https://{server}:{port}"
    
    print(f"Testing connection to: {server_url}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test 1: Network connectivity
    print("1. Testing network connectivity...")
    if test_network_connectivity(server, port):
        print(f"   ✅ Network connection to {server}:{port} successful")
    else:
        print(f"   ❌ Network connection to {server}:{port} failed")
        print(f"   💡 Check if FileMaker Server is running and accessible")
        return
    
    # Test 2: FileMaker API authentication
    print("\n2. Testing FileMaker Data API authentication...")
    auth_result = test_filemaker_auth(server_url, database, username, password)
    
    if auth_result['success']:
        print(f"   ✅ Authentication successful")
        print(f"   📊 Status Code: {auth_result['status_code']}")
    else:
        print(f"   ❌ Authentication failed")
        if 'error' in auth_result:
            print(f"   🚨 Error: {auth_result['error']}")
        else:
            print(f"   📊 Status Code: {auth_result['status_code']}")
            print(f"   📝 Response: {auth_result['response']}")
    
    print("\n" + "=" * 60)
    
if __name__ == "__main__":
    main()

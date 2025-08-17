#!/usr/bin/env python3
"""
Test FileMaker Server authentication methods and capabilities
"""

import requests
import json
import urllib3
import base64

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_basic_auth_header():
    """Test with Authorization header instead of JSON body"""
    print("=== Testing Basic Auth with Authorization Header ===")
    
    server = "192.168.0.108"
    port = 443
    database = "PreInventory"
    username = "JSON"
    password = "Windu63Purple!"
    
    # Create basic auth header
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    auth_url = f"https://{server}:{port}/fmi/data/v1/databases/{database}/sessions"
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            auth_url,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Basic Auth with header works!")
            return response.json()['response']['token']
        else:
            print("❌ Basic Auth with header failed")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_data_api_info():
    """Get Data API information"""
    print("\n=== Testing Data API Info Endpoint ===")
    
    server = "192.168.0.108"
    port = 443
    
    info_url = f"https://{server}:{port}/fmi/data/v1/productInfo"
    
    try:
        response = requests.get(
            info_url,
            verify=False,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            info = response.json()
            print("✅ Product info retrieved successfully")
            return info
        else:
            print("❌ Failed to get product info")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_databases_endpoint():
    """Test the databases endpoint to see what auth is needed"""
    print("\n=== Testing Databases Endpoint ===")
    
    server = "192.168.0.108"
    port = 443
    
    databases_url = f"https://{server}:{port}/fmi/data/v1/databases"
    
    try:
        response = requests.get(
            databases_url,
            verify=False,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Databases endpoint accessible without auth")
            return response.json()
        else:
            print("❌ Databases endpoint requires auth or failed")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_oauth_discovery():
    """Check for OAuth discovery endpoints"""
    print("\n=== Testing OAuth Discovery ===")
    
    server = "192.168.0.108"
    port = 443
    
    oauth_endpoints = [
        f"https://{server}:{port}/.well-known/oauth-authorization-server",
        f"https://{server}:{port}/oauth/authorize",
        f"https://{server}:{port}/fmi/oauth/authorize",
        f"https://{server}:{port}/oauth/token",
        f"https://{server}:{port}/fmi/oauth/token"
    ]
    
    for endpoint in oauth_endpoints:
        try:
            response = requests.get(
                endpoint,
                verify=False,
                timeout=10
            )
            
            print(f"Endpoint: {endpoint}")
            print(f"Status: {response.status_code}")
            if response.status_code < 400:
                print(f"Response: {response.text[:200]}...")
            print()
            
        except Exception as e:
            print(f"Endpoint: {endpoint} - Error: {str(e)}")

if __name__ == "__main__":
    print("=== FileMaker Authentication Method Testing ===")
    
    # Test product info (should work without auth)
    test_data_api_info()
    
    # Test databases endpoint
    test_databases_endpoint()
    
    # Test basic auth with header
    test_basic_auth_header()
    
    # Test OAuth discovery
    test_oauth_discovery()
    
    print("\n=== Testing Complete ===")
    print("\nNote: If all authentication methods fail, the FileMaker Data API")
    print("might be disabled or configured for external OAuth provider.")

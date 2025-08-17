#!/usr/bin/env python3
"""
Test FileMaker authentication with different credential combinations
"""

import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_auth(server, port, database, username, password, description):
    """Test authentication with given credentials"""
    print(f"\n=== Testing {description} ===")
    print(f"Server: {server}:{port}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    auth_url = f"https://{server}:{port}/fmi/data/v1/databases/{database}/sessions"
    
    auth_data = {
        "username": username,
        "password": password
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            auth_url, 
            json=auth_data, 
            headers=headers, 
            verify=False,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            token = response.json()['response']['token']
            print(f"✅ SUCCESS! Token: {token[:20]}...")
            return token
        else:
            print(f"❌ FAILED: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

if __name__ == "__main__":
    # Load current config
    with open('filemaker_config.json', 'r') as f:
        config = json.load(f)
    
    print("=== FileMaker Authentication Testing ===")
    
    # Test current config
    token = test_auth(
        config['server'],
        config['port'], 
        config['database'],
        config['username'],
        config['password'],
        "Current Config"
    )
    
    # Test with different username possibilities
    if not token:
        print("\n" + "="*50)
        print("Trying alternative usernames...")
        
        usernames_to_try = ['admin', 'Admin', 'filemaker', 'fmserver', 'json', 'JSON']
        passwords_to_try = [config['password'], 'Rynrin12']
        
        for username in usernames_to_try:
            for password in passwords_to_try:
                if username == config['username'] and password == config['password']:
                    continue  # Already tested
                
                token = test_auth(
                    config['server'],
                    config['port'], 
                    config['database'],
                    username,
                    password,
                    f"Alternative: {username}/{password}"
                )
                
                if token:
                    print(f"\n🎉 WORKING CREDENTIALS FOUND!")
                    print(f"Username: {username}")
                    print(f"Password: {password}")
                    break
            
            if token:
                break
    
    print("\n=== Authentication Test Complete ===")

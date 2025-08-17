#!/usr/bin/env python3
"""
Simple test to verify FileMaker script parameter passing
"""

import os
import sys
import json
from datetime import datetime

# Add the dashboard directory to Python path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_script_parameters():
    """Test script parameter passing to PDFTimesheet"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        config_path = '/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Create FileMaker instance
        server_url = f"https://{config['server']}:{config['port']}"
        fm = FileMakerIntegration(
            server_url=server_url,
            database=config['database'],
            username=config['username'],
            password=config['password'],
            ssl_verify=config.get('ssl_verify', True)
        )
        
        if not fm.authenticate():
            print("❌ Authentication failed")
            return False
        
        print("✅ Authentication successful")
        
        # Get a test record
        layout = config['layout']
        records = fm.get_all_records(layout, limit=1)
        
        if not records:
            print("❌ No records found")
            return False
        
        record_id = records[0].get('recordId')
        print(f"📄 Testing with record ID: {record_id}")
        
        # Test different parameter formats
        test_cases = [
            {
                "name": "Simple test parameter",
                "params": "test123"
            },
            {
                "name": "Mac file path",
                "params": f"{record_id}|{layout}|/Users/Shared/ParkerPOsOCR/exports/test.pdf"
            },
            {
                "name": "Desktop path",
                "params": f"{record_id}|{layout}|~/Desktop/test.pdf"
            },
            {
                "name": "Temp path",
                "params": f"{record_id}|{layout}|/tmp/test.pdf"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n📝 Testing: {test_case['name']}")
            print(f"   Parameters: {test_case['params']}")
            
            try:
                result = fm.run_script_on_record(
                    record_id,
                    "PDFTimesheet",
                    test_case['params'],
                    layout
                )
                print(f"   Result: {result}")
            except Exception as e:
                print(f"   Error: {e}")
        
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== FileMaker Script Parameter Test ===")
    test_script_parameters()
    print("=" * 45)

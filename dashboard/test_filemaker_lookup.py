#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_filemaker_lookup():
    """Test FileMaker integration with lookup script"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== FileMaker Lookup Test ===")
        print(f"Server: {config['server']}:{config['port']}")
        print(f"Database: {config['database']}")
        print(f"Lookup Script: {config.get('lookup_script', 'None')}")
        print(f"Trigger Lookups: {config.get('trigger_lookups', False)}")
        print("-" * 50)
        
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
        
        # Test authentication
        print("1. Testing authentication...")
        if fm.authenticate():
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed!")
            return False
        
        # Test record creation with lookup script
        print("\n2. Testing record creation with lookup script...")
        
        test_data = {
            "Whittaker Shipper #": "TEST_PO_999999",
            "PART NUMBER": "450130*OP40",  # Use a known part number
            "QTY SHIP": "1",
            "MJO NO": "TEST_MJO_999",
            "Promise Delivery Date": "08/15/2025",
            "Planner Name": "Nora Seclen"
        }
        
        print(f"Test data: {test_data}")
        print("Creating record...")
        
        record_id = fm.create_record(test_data, config['layout'], config)
        
        if record_id:
            print(f"✅ Test record created successfully! Record ID: {record_id}")
            print("The lookup script should have been triggered automatically.")
            print("Check FileMaker to see if Description, Revision, and Op Sheet Issue are populated.")
            return True
        else:
            print("❌ Failed to create test record")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_filemaker_lookup()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")

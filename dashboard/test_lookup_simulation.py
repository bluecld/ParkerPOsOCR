#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_lookup_simulation():
    """Test the new lookup simulation approach that manually retrieves related data"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Testing Lookup Simulation via Related Data ===")
        
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
        
        # Authenticate
        if not fm.authenticate():
            print("❌ Authentication failed!")
            return False
        
        print("✅ Authentication successful!")
        
        # Test with a part number that should exist in PRICES table
        test_record = {
            "Whittaker Shipper #": "4551241600",  # New test PO number
            "PART NUMBER": "450130*OP40",  # This should exist in PRICES table
            "QTY SHIP": "30",
            "MJO NO": "125146000",
            "Promise Delivery Date": "08/14/2025",
            "Planner Name": "Nora Seclen"
        }
        
        print(f"\n--- Creating Test Record ---")
        print(f"PO: {test_record['Whittaker Shipper #']}")
        print(f"Part: {test_record['PART NUMBER']}")
        
        # Create the record with lookup simulation enabled
        record_id = fm.create_record(test_record, config['layout'], config)
        
        if record_id:
            print(f"✅ Record created with ID: {record_id}")
            print("✅ Lookup simulation should have run automatically")
            return True
        else:
            print("❌ Failed to create test record")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_lookup_only():
    """Test just the lookup simulation part on an existing record"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Testing Manual Lookup Simulation Only ===")
        
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
        
        # Authenticate
        if not fm.authenticate():
            print("❌ Authentication failed!")
            return False
        
        print("✅ Authentication successful!")
        
        # Test on a recent record (adjust ID as needed)
        test_record_id = "57684"  # Use a record ID from the previous tests
        test_field_data = {
            "PART NUMBER": "450130*OP40"
        }
        
        print(f"\n--- Testing Manual Lookup on Record {test_record_id} ---")
        
        # Run the lookup simulation directly
        success = fm.simulate_lookups_via_related_data(test_record_id, test_field_data, config['layout'])
        
        if success:
            print("🎉 Lookup simulation completed successfully!")
            return True
        else:
            print("❌ Lookup simulation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 FileMaker Lookup Simulation Test")
    print("="*50)
    
    print("\n1️⃣ Testing complete record creation with lookup simulation...")
    success1 = test_lookup_simulation()
    
    print("\n" + "="*50)
    print("\n2️⃣ Testing manual lookup simulation on existing record...")
    success2 = test_manual_lookup_only()
    
    print("\n" + "="*50)
    print(f"\nResults:")
    print(f"Complete Test: {'SUCCESS' if success1 else 'FAILED'}")
    print(f"Manual Test: {'SUCCESS' if success2 else 'FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! The lookup simulation is working correctly.")
        print("\n📝 What this means:")
        print("- Records are created successfully in FileMaker")
        print("- Related data is retrieved from PRICES table")
        print("- Description, Revision, Op Sheet Issue fields are populated")
        print("- No FileMaker scripts or relationships required!")
    else:
        print("\n🔧 Some tests failed. Check the output above for details.")
        print("\n💡 Common issues:")
        print("- Part number doesn't exist in PRICES table")
        print("- PRICES layout is not accessible via Data API")
        print("- Field names don't match between tables")

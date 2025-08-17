#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_filemaker_script():
    """Test FileMaker script execution and show detailed results"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== FileMaker Script Test ===")
        
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
        
        # Test data
        test_po = "4551241597"
        test_part = "450130*OP40"
        
        print(f"\n--- Testing Script Execution ---")
        print(f"PO Number: {test_po}")
        print(f"Part Number: {test_part}")
        
        # First, let's create a test record
        record_data = {
            "Whittaker Shipper #": test_po,
            "PART NUMBER": test_part,
            "QTY SHIP": "13",
            "MJO NO": "125145318",
            "Promise Delivery Date": "08/14/2025",
            "Planner Name": "Nora Seclen"
        }
        
        print(f"\n--- Creating Test Record ---")
        record_id = fm.create_record(record_data, config['layout'], config)
        
        if record_id:
            print(f"✅ Test record created! ID: {record_id}")
            
            # Now run the lookup script directly
            print(f"\n--- Running Lookup Script Directly ---")
            script_params = f"{test_po}|{test_part}"
            script_result = fm.run_script_on_record(record_id, "Lookup", script_params)
            
            print(f"Script Parameters: {script_params}")
            print(f"Script Result: {script_result}")
            
            # Get the record to see current field values
            print(f"\n--- Checking Final Field Values ---")
            record = fm.get_record(record_id)
            
            if record:
                fields = record.get('fieldData', {})
                print(f"Part Number: {fields.get('PART NUMBER', 'EMPTY')}")
                print(f"Description: {fields.get('Description', 'EMPTY')}")
                print(f"Revision: {fields.get('Revision', 'EMPTY')}")
                print(f"Op Sheet Issue: {fields.get('Op Sheet Issue', 'EMPTY')}")
                
                # Check if lookups worked
                if fields.get('Description') and fields.get('Revision'):
                    print("✅ LOOKUPS WORKED!")
                else:
                    print("❌ LOOKUPS FAILED - Fields are empty")
            else:
                print("❌ Could not retrieve record after script execution")
                
        else:
            print("❌ Failed to create test record")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_filemaker_script()

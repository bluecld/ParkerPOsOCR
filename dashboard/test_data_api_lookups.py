#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_data_api_lookups():
    """Test the new Data API lookup approach"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== Testing Data API Lookup Approach ===")
        
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
        
        # Test record data
        test_record = {
            "Whittaker Shipper #": "4551241599",  # New test PO number
            "PART NUMBER": "450130*OP40",
            "QTY SHIP": "25",
            "MJO NO": "125145999",
            "Promise Delivery Date": "08/14/2025",
            "Planner Name": "Nora Seclen"
        }
        
        print(f"\n--- Creating Test Record ---")
        print(f"PO: {test_record['Whittaker Shipper #']}")
        print(f"Part: {test_record['PART NUMBER']}")
        
        # Create the record with lookup triggering enabled
        record_id = fm.create_record(test_record, config['layout'], config)
        
        if record_id:
            print(f"✅ Record created with ID: {record_id}")
            
            # The lookups should have been triggered automatically
            # Let's verify by getting the final record
            print(f"\n--- Final Verification ---")
            final_record = fm.get_record(record_id, config['layout'])
            
            if final_record:
                fields = final_record.get('fieldData', {})
                print(f"\n📋 Final Record State:")
                print(f"  Record ID: {record_id}")
                print(f"  PO Number: {fields.get('Whittaker Shipper #', 'EMPTY')}")
                print(f"  Part Number: {fields.get('PART NUMBER', 'EMPTY')}")
                print(f"  Description: {fields.get('Description', 'EMPTY')}")
                print(f"  Revision: {fields.get('Revision', 'EMPTY')}")
                print(f"  Op Sheet Issue: {fields.get('Op Sheet Issue', 'EMPTY')}")
                print(f"  Quantity: {fields.get('QTY SHIP', 'EMPTY')}")
                print(f"  MJO: {fields.get('MJO NO', 'EMPTY')}")
                print(f"  Planner: {fields.get('Planner Name', 'EMPTY')}")
                
                # Check results
                if fields.get('Description') and fields.get('Revision'):
                    print("\n🎉 SUCCESS: All lookups populated correctly!")
                    print("The Data API approach is working!")
                    return True
                else:
                    print(f"\n⚠️ PARTIAL SUCCESS: Record created but lookups not populated")
                    print("This might indicate a relationship or field configuration issue in FileMaker")
                    return False
            else:
                print("❌ Could not retrieve final record for verification")
                return False
        else:
            print("❌ Failed to create test record")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_api_lookups()
    print(f"\n{'='*50}")
    print(f"Test Result: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. The Data API approach is working!")
        print("2. You can now use the dashboard to create FileMaker records")
        print("3. All lookups should populate automatically")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check FileMaker relationship: PreInventory::PART NUMBER ↔ PRICES::PART NUMBER")
        print("2. Verify Description, Revision, Op Sheet Issue are configured as lookup fields")
        print("3. Ensure both field types are Text and match exactly")

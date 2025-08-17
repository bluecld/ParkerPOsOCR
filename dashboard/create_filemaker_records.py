#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def create_sample_records():
    """Create sample records in FileMaker using the API"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        print("=== FileMaker Record Creation ===")
        
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
        
        # Sample records to create
        sample_records = [
            {
                "Whittaker Shipper #": "4551241597",
                "PART NUMBER": "450130*OP40",
                "QTY SHIP": "13",
                "MJO NO": "125145318",
                "Promise Delivery Date": "08/14/2025",
                "Planner Name": "Nora Seclen"
            },
            {
                "Whittaker Shipper #": "4551241598", 
                "PART NUMBER": "450130*OP40",
                "QTY SHIP": "20",
                "MJO NO": "125089337",
                "Promise Delivery Date": "08/14/2025",
                "Planner Name": "Nora Seclen"
            }
        ]
        
        created_records = []
        
        for i, record_data in enumerate(sample_records):
            print(f"\n--- Creating Record {i+1} ---")
            print(f"PO: {record_data['Whittaker Shipper #']}")
            print(f"Part: {record_data['PART NUMBER']}")
            print(f"Qty: {record_data['QTY SHIP']}")
            print(f"Planner: {record_data['Planner Name']}")
            
            record_id = fm.create_record(record_data, config['layout'], config)
            
            if record_id:
                print(f"✅ Record created successfully! ID: {record_id}")
                created_records.append({
                    'record_id': record_id,
                    'po_number': record_data['Whittaker Shipper #'],
                    'part_number': record_data['PART NUMBER']
                })
            else:
                print(f"❌ Failed to create record for PO {record_data['Whittaker Shipper #']}")
        
        print(f"\n=== Summary ===")
        print(f"Created {len(created_records)} records successfully:")
        for record in created_records:
            print(f"  - Record {record['record_id']}: PO {record['po_number']} ({record['part_number']})")
        
        print("\n📝 Next Steps:")
        print("1. Check FileMaker to verify records were created")
        print("2. Verify that Description, Revision, Op Sheet Issue fields are populated")
        print("3. If lookup fields are empty, update your 'Lookup' script in FileMaker")
        
        return len(created_records) > 0
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_sample_records()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")

#!/usr/bin/env python3
"""
Test to check FileMaker script execution and diagnose PDFTimesheet issues
"""

import os
import sys
import json
from datetime import datetime

# Add the dashboard directory to Python path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_script_execution():
    """Test script execution to diagnose PDFTimesheet issues"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        config_path = '/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("🔧 Creating FileMaker integration instance...")
        
        # Create FileMaker instance
        server_url = f"https://{config['server']}:{config['port']}"
        fm = FileMakerIntegration(
            server_url=server_url,
            database=config['database'],
            username=config['username'],
            password=config['password'],
            ssl_verify=config.get('ssl_verify', True)
        )
        
        print("🔐 Authenticating with FileMaker...")
        
        # Authenticate
        if not fm.authenticate():
            print("❌ Authentication failed")
            return False
        
        print("✅ Authentication successful")
        
        # Get records from Time Clock layout
        print("📋 Getting records from Time Clock layout...")
        layout = config['layout']
        records = fm.get_all_records(layout, limit=1)
        
        if not records:
            print("❌ No records found in Time Clock layout")
            return False
        
        # Test with the first record
        test_record = records[0]
        record_id = test_record.get('recordId')
        
        print(f"📄 Testing with record ID: {record_id}")
        print(f"📄 Record data: {test_record.get('fieldData', {})}")
        
        # Test different script execution approaches
        scripts_to_test = [
            ("PDFTimesheet", None),
            ("PDFTimesheet", ""),
            ("PDFTimesheet", "test"),
            ("Lookup", None),  # Try a different script that might exist
        ]
        
        for script_name, params in scripts_to_test:
            print(f"\n📝 Testing script: '{script_name}' with params: {params}")
            try:
                script_result = fm.run_script_on_record(
                    record_id, 
                    script_name,
                    params,
                    layout
                )
                print(f"   ✅ Script result: {script_result}")
            except Exception as e:
                print(f"   ❌ Script error: {e}")
        
        # Also try to get more info about the record structure
        print(f"\n🔍 Detailed record information:")
        detailed_record = fm.get_record(record_id, layout)
        if detailed_record:
            field_data = detailed_record.get('fieldData', {})
            print(f"   Fields available: {list(field_data.keys())}")
            for field, value in list(field_data.items())[:5]:  # Show first 5 fields
                print(f"   {field}: {value}")
        
        return True
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== FileMaker Script Execution Diagnostics ===")
    success = test_script_execution()
    
    if success:
        print("\n✅ Diagnostics completed!")
    else:
        print("\n❌ Diagnostics failed!")
    
    print("=" * 50)

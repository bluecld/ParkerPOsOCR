#!/usr/bin/env python3
"""
Simple test script for PDFTimesheet script execution
"""

import os
import sys
import json
from datetime import datetime

# Add the dashboard directory to Python path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_pdf_script():
    """Test PDFTimesheet script execution"""
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
        records = fm.get_all_records(layout, limit=3)
        
        if not records:
            print("❌ No records found in Time Clock layout")
            return False
        
        # Test with the first record
        test_record = records[0]
        record_id = test_record.get('recordId')
        
        print(f"📄 Testing PDFTimesheet script with record ID: {record_id}")
        
        # Test the script with minimal parameters
        print("📝 Running PDFTimesheet script...")
        script_result = fm.run_script_on_record(
            record_id, 
            "PDFTimesheet",
            f"record_{record_id}",  # Simple parameter
            layout
        )
        
        print(f"Script execution result: {script_result}")
        
        # Also try running the script without parameters
        print("📝 Running PDFTimesheet script without parameters...")
        script_result2 = fm.run_script_on_record(
            record_id, 
            "PDFTimesheet",
            None,  # No parameters
            layout
        )
        
        print(f"Script execution result (no params): {script_result2}")
        
        return True
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== PDFTimesheet Script Test ===")
    success = test_pdf_script()
    
    if success:
        print("\n✅ Script test completed!")
    else:
        print("\n❌ Script test failed!")
    
    print("=" * 40)

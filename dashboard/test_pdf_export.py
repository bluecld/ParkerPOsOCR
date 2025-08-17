#!/usr/bin/env python3
"""
Test script for PDF export functionality
"""

import os
import sys
import json
from datetime import datetime

# Add the dashboard directory to Python path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_pdf_export():
    """Test PDF export functionality"""
    try:
        from filemaker_integration import FileMakerIntegration
        
        # Load configuration
        config_path = '/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("🔧 Creating FileMaker integration instance...")
        
        # Create FileMaker instance with the correct config structure
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
        
        # Get all records to find one for testing
        print("📋 Getting available records...")
        layout = config['layout']
        records = fm.get_all_records(layout, limit=5)
        
        if not records:
            print("❌ No records found for testing")
            return False
        
        # Get the first record ID for testing
        test_record = records[0]
        record_id = test_record.get('recordId')
        
        if not record_id:
            print("❌ No valid record ID found")
            return False
        
        print(f"📄 Testing PDF export for record ID: {record_id}")
        
        # Test get_record_for_export
        print("📊 Getting record data for export...")
        export_data = fm.get_record_for_export(record_id, layout)
        
        if export_data:
            print("✅ Record data retrieved:")
            for key, value in export_data.items():
                print(f"   {key}: {value}")
        else:
            print("❌ Failed to get record data")
            return False
        
        # Test PDF export
        print("📤 Attempting PDF export...")
        pdf_path = fm.export_record_as_pdf(record_id, layout)
        
        if pdf_path:
            print(f"✅ PDF export successful: {pdf_path}")
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"📄 File size: {file_size} bytes")
                return True
            else:
                print("❌ PDF file was not created")
                return False
        else:
            print("❌ PDF export failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== FileMaker PDF Export Test ===")
    success = test_pdf_export()
    
    if success:
        print("\n✅ PDF export test completed successfully!")
    else:
        print("\n❌ PDF export test failed!")
    
    print("=" * 40)

#!/usr/bin/env python3
"""
Test to compare PDFTimesheet with other scripts to isolate the issue
"""

import os
import sys
import json
from datetime import datetime

# Add the dashboard directory to Python path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_script_comparison():
    """Test PDFTimesheet against other scripts to isolate the issue"""
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
        
        # Test different scripts for comparison
        test_scripts = [
            ("Lookup", None, "Known working script"),
            ("PDFTimesheet", None, "PDF script - no params"),
            ("PDFTimesheet", "simple", "PDF script - simple param"),
            ("PDFTimesheet", f"/tmp/test_{record_id}.pdf", "PDF script - simple path only"),
        ]
        
        for script_name, params, description in test_scripts:
            print(f"\n📝 Testing: {description}")
            print(f"   Script: {script_name}")
            print(f"   Parameters: {params}")
            
            try:
                result = fm.run_script_on_record(
                    record_id,
                    script_name,
                    params,
                    layout
                )
                print(f"   ✅ Result: {result if result else 'Empty result'}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Try calling the script with minimal parameters
        print(f"\n🔬 Advanced test: PDFTimesheet with just filename")
        try:
            simple_filename = f"test_{record_id}.pdf"
            result = fm.run_script_on_record(
                record_id,
                "PDFTimesheet", 
                simple_filename,  # Just filename, let script handle path
                layout
            )
            print(f"   Result with filename only: {result}")
        except Exception as e:
            print(f"   Error: {e}")
        
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== FileMaker Script Comparison Test ===")
    test_script_comparison()
    print("=" * 50)

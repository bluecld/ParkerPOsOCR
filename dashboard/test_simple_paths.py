#!/usr/bin/env python3
"""
Test PDFTimesheet with various simple file path approaches
"""

import os
import sys
import json

sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

def test_simple_paths():
    try:
        from filemaker_integration import FileMakerIntegration
        
        with open('/volume1/Main/Main/ParkerPOsOCR/dashboard/filemaker_config.json', 'r') as f:
            config = json.load(f)
        
        server_url = f"https://{config['server']}:{config['port']}"
        fm = FileMakerIntegration(
            server_url=server_url,
            database=config['database'],
            username=config['username'],
            password=config['password'],
            ssl_verify=False
        )
        
        if not fm.authenticate():
            print("❌ Auth failed")
            return
        
        print("✅ Authenticated")
        
        record_id = "57703"
        layout = config['layout']
        
        # Test with various simple path formats
        test_paths = [
            "test.pdf",  # Just filename
            "/tmp/test.pdf",  # Temp directory
            "~/Desktop/test.pdf",  # Home desktop
            "/Users/Shared/test.pdf",  # Shared folder
            "filemac:///Users/Shared/test.pdf",  # Mac file protocol
            "/var/tmp/test.pdf",  # Alternative temp
        ]
        
        for test_path in test_paths:
            print(f"\n📝 Testing path: {test_path}")
            
            # Use the run_script_on_record method
            try:
                result = fm.run_script_on_record(
                    record_id,
                    "PDFTimesheet",
                    test_path,  # Just the file path as parameter
                    layout
                )
                print(f"   Result: {result if result else 'Empty result'}")
            except Exception as e:
                print(f"   Error: {e}")
        
        # Also test with no parameters at all
        print(f"\n📝 Testing with NO parameters")
        try:
            result = fm.run_script_on_record(
                record_id,
                "PDFTimesheet",
                None,  # No parameters
                layout
            )
            print(f"   Result: {result if result else 'Empty result'}")
        except Exception as e:
            print(f"   Error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== Simple Path Test ===")
    test_simple_paths()
    print("=" * 30)

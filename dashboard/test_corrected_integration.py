#!/usr/bin/env python3
"""
Test the corrected FileMaker integration with the PDF export script
"""

import json
import sys
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/dashboard')

from filemaker_integration import FileMakerIntegration

def test_corrected_integration():
    """Test the corrected FileMaker integration"""
    print("🧪 === Testing Corrected FileMaker Integration ===\n")
    
    # Load configuration
    with open('filemaker_config.json', 'r') as f:
        config = json.load(f)
    
    # Create integration instance
    server_url = f"https://{config['server']}:{config['port']}"
    fm = FileMakerIntegration(
        server_url=server_url,
        database=config['database'],
        username=config['username'],
        password=config['password'],
        ssl_verify=config.get('ssl_verify', False),
        timeout=config.get('timeout', 30)
    )
    
    # Test authentication
    print("🔐 Testing authentication...")
    auth_success = fm.authenticate()
    
    if not auth_success:
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful!\n")
    
    # Test PDF export on a specific record
    record_id = "57704"  # Use a known record ID
    layout_name = config['layout']
    
    print(f"📄 Testing PDF export on record {record_id}...")
    
    try:
        result = fm.export_via_script(record_id, layout_name)
        
        if result:
            print(f"✅ PDF export successful!")
            print(f"📁 Result: {result}")
            return True
        else:
            print("❌ PDF export failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during PDF export: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 Testing Corrected FileMaker PDF Export Integration")
    print("=" * 60)
    
    success = test_corrected_integration()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULT:")
    print(f"✅ Integration Test: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print("\n🎉 SUCCESS! The corrected integration is working!")
        print("💡 Your FileMaker script is being called correctly.")
        print("📄 PDF should be created in the server's Documents folder.")
    else:
        print("\n❌ Integration test failed")
        print("💡 Check FileMaker script and server configuration")
        
    print("=" * 60)

#!/usr/bin/env python3
"""
Test script to verify PDF generation is working
"""
import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

from filemaker_integration import FileMakerIntegration
import json

def test_pdf_generation():
    """Test PDF generation with a sample PO"""
    
    # Test with the PO that worked: 4551240642
    test_po = "4551240642"
    print(f"Testing PDF generation for PO: {test_po}")
    
    # Initialize FileMaker integrator
    fm = FileMakerIntegration()
    
    # Test data for the PO that worked
    test_data = {
        "purchase_order_number": test_po,
        "production_order": "125144071", 
        "revision": "G",
        "part_number": "521350-2",
        "quantity": 50,
        "dock_date": "07/31/2025",
        "payment_terms": "30 Days from Date of Invoice",
        "payment_terms_non_standard_flag": False,
        "vendor_name": "TEK ENTERPRISES, INC.",
        "vendor_non_tek_flag": False,
        "buyer_name": "Buyer"
    }
    
    try:
        print("Attempting to submit PO and generate PDF...")
        result = fm.insert_po_data(test_data)
        
        if result.get('success'):
            print(f"✅ SUCCESS: {result}")
            print(f"RecordId: {result.get('record_id')}")
            print(f"Script Error: {result.get('script_error', 'Not reported')}")
        else:
            print(f"❌ FAILED: {result}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()

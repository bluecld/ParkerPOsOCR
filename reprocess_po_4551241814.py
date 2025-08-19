#!/usr/bin/env python3
"""
Re-extract PO 4551241814 with enhanced part number validation
"""

import sys
import json
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

from extract_po_details import extract_po_details_and_create_json

def reprocess_po_4551241814():
    """Re-process PO 4551241814 with the enhanced validation"""
    
    po_number = "4551241814"
    pdf_path = f"/volume1/Main/Main/ParkerPOsOCR/POs/{po_number}/PO_{po_number}.pdf"
    output_dir = f"/volume1/Main/Main/ParkerPOsOCR/POs/{po_number}"
    
    print(f"Re-processing {po_number} with enhanced part number validation...")
    print("=" * 60)
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
        
    # Read current results for comparison
    current_json_path = f"{output_dir}/{po_number}_info.json"
    if os.path.exists(current_json_path):
        with open(current_json_path, 'r') as f:
            current_data = json.load(f)
        print(f"Current part number: {current_data.get('part_number', 'NOT FOUND')}")
    else:
        print("No current JSON file found")
        current_data = {}
        
    # Re-extract with enhanced validation
    print("\nRe-extracting with validation...")
    try:
        result = extract_po_details_and_create_json(pdf_path, output_dir)
        
        if result:
            # Load the new results
            with open(current_json_path, 'r') as f:
                new_data = json.load(f)
                
            print("\n📊 COMPARISON RESULTS:")
            print("=" * 30)
            print(f"Old part number: {current_data.get('part_number', 'N/A')}")  
            print(f"New part number: {new_data.get('part_number', 'N/A')}")
            
            # Check if it improved
            old_part = current_data.get('part_number', '')
            new_part = new_data.get('part_number', '')
            
            if old_part != new_part:
                print(f"✅ IMPROVEMENT: {old_part} → {new_part}")
            else:
                print("ℹ️  No change in part number")
                
        else:
            print("❌ Re-extraction failed")
            
    except Exception as e:
        print(f"❌ Error during re-extraction: {e}")

if __name__ == "__main__":
    reprocess_po_4551241814()

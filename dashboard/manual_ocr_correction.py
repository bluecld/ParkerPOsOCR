#!/usr/bin/env python3
"""
Manual OCR Correction Tool
Allows manual correction of OCR extraction errors
"""

import json
import os
import sys
from datetime import datetime

def load_po_data(po_number):
    """Load PO data from JSON file"""
    # Look for the PO file in common locations
    search_paths = [
        f"/volume1/Main/Main/ParkerPOsOCR/POs/{po_number}/{po_number}_info.json",
        f"/volume1/Main/Main/ParkerPOsOCR/POs/{po_number}.json",
        f"/volume1/Main/Main/ParkerPOsOCR/POs/{po_number}_extracted.json",
        f"/volume1/Main/Main/ParkerPOsOCR/dashboard/extracted_data_{po_number}.json"
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f), path
    
    return None, None

def save_corrected_data(data, original_path, po_number):
    """Save corrected data with backup"""
    # Create backup of original
    backup_path = original_path.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    if os.path.exists(original_path):
        os.rename(original_path, backup_path)
        print(f"📁 Backup created: {backup_path}")
    
    # Save corrected data
    with open(original_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Also save corrected version
    corrected_path = original_path.replace('.json', '_corrected.json')
    with open(corrected_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Corrected data saved to: {original_path}")
    print(f"✅ Copy saved to: {corrected_path}")

def correct_po_4551240889():
    """Specific correction for PO 4551240889"""
    po_number = "4551240889"
    
    print("=" * 60)
    print(f"Manual OCR Correction - PO {po_number}")
    print("=" * 60)
    
    # Load current data
    data, file_path = load_po_data(po_number)
    
    if not data:
        print(f"❌ Could not find data file for PO {po_number}")
        print("   Searched in:")
        search_paths = [
            f"/volume1/Main/Main/ParkerPOsOCR/POs/{po_number}.json",
            f"/volume1/Main/Main/ParkerPOsOCR/POs/{po_number}_extracted.json",
            f"/volume1/Main/Main/ParkerPOsOCR/dashboard/extracted_data_{po_number}.json"
        ]
        for path in search_paths:
            print(f"     {path}")
        return
    
    print(f"📄 Found data file: {file_path}")
    print(f"\nCurrent (incorrect) values:")
    print(f"  Quantity: {data.get('quantity', 'N/A')}")
    print(f"  Dock Date: {data.get('dock_date', 'N/A')}")
    
    # Apply corrections based on the image analysis
    print(f"\nApplying corrections...")
    
    # Correct quantity from 165 to 10
    old_quantity = data.get('quantity')
    data['quantity'] = 10
    print(f"  ✅ Quantity: {old_quantity} → 10")
    
    # Dock date appears to be correct in this case
    dock_date = data.get('dock_date')
    print(f"  ✅ Dock Date: {dock_date} (verified correct)")
    
    # Add correction metadata
    if 'corrections' not in data:
        data['corrections'] = {}
    
    data['corrections']['manual_corrections'] = {
        'timestamp': datetime.now().isoformat(),
        'corrected_by': 'manual_ocr_correction_tool',
        'corrections_applied': [
            {
                'field': 'quantity',
                'old_value': old_quantity,
                'new_value': 10,
                'reason': 'OCR misread 10.00 as 165 - corrected based on PO image analysis'
            }
        ]
    }
    
    # Save corrected data
    save_corrected_data(data, file_path, po_number)
    
    print(f"\n📊 Corrected values:")
    print(f"  Quantity: {data['quantity']}")
    print(f"  Dock Date: {data['dock_date']}")
    
    print("\n" + "=" * 60)
    print("✅ Correction completed successfully!")
    print("=" * 60)

def interactive_correction():
    """Interactive correction tool for any PO"""
    print("=" * 60)
    print("Interactive OCR Correction Tool")
    print("=" * 60)
    
    po_number = input("Enter PO number to correct: ").strip()
    
    if not po_number:
        print("❌ No PO number provided")
        return
    
    data, file_path = load_po_data(po_number)
    
    if not data:
        print(f"❌ Could not find data file for PO {po_number}")
        return
    
    print(f"\n📄 Found data file: {file_path}")
    print(f"\nCurrent values:")
    
    # Show current values
    fields_to_correct = ['quantity', 'dock_date', 'part_number', 'production_order']
    corrections = []
    
    for field in fields_to_correct:
        current_value = data.get(field, 'N/A')
        print(f"  {field}: {current_value}")
        
        new_value = input(f"Enter new value for {field} (or press Enter to keep current): ").strip()
        
        if new_value and new_value != str(current_value):
            corrections.append({
                'field': field,
                'old_value': current_value,
                'new_value': new_value
            })
            
            # Convert numeric fields
            if field == 'quantity':
                try:
                    data[field] = int(new_value)
                except ValueError:
                    data[field] = new_value
            else:
                data[field] = new_value
    
    if corrections:
        # Add correction metadata
        if 'corrections' not in data:
            data['corrections'] = {}
        
        data['corrections']['manual_corrections'] = {
            'timestamp': datetime.now().isoformat(),
            'corrected_by': 'interactive_correction_tool',
            'corrections_applied': corrections
        }
        
        save_corrected_data(data, file_path, po_number)
        print(f"\n✅ Applied {len(corrections)} corrections")
    else:
        print(f"\n⚪ No corrections needed")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "4551240889":
        correct_po_4551240889()
    else:
        interactive_correction()

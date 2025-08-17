#!/usr/bin/env python3
"""
Test OCR Extraction Improvements
Test the corrected quantity and dock date extraction
"""

import sys
import os
import json
import re
from datetime import datetime

# Mock the OCR text based on the image provided
SAMPLE_OCR_TEXT = """
Item    Part number                 Revision  Quantity    Net    Per  UM  Dock date    Net
        description                                       price              amount
PURCHASE ORDER ACKNOWLEDGEMENT REQUIRED

10                                            10.00      16.50        EA  09/03/2025 165.00
154370-8 OP20 ASSEMBLY
Production Order        125157207
154370-8 REV N PLATE ASSY

Delivery Date                     Quantity                         UM
09/03/2025                       10.00                           EA

ASSEMBLY
OP TO FOLLOW CMPD154370-8
CAUTION: TARNISH ON ARMS WILL BE CAUSE FOR REJECTION.
"""

def extract_quantity_and_dock_date(text):
    """Extract quantity as whole number and dock date from the same context"""
    quantity = None
    dock_date = None
    
    lines = text.split('\n')
    
    # Strategy 1: Look for table structure with quantity and dock date
    # Based on the image: Item | Part number | Revision | Quantity | Net price | Per | UM | Dock date | Net amount
    for i, line in enumerate(lines):
        # Look for lines that contain quantity patterns
        # Check for decimal numbers (like 10.00) which represent quantities
        qty_matches = re.findall(r'(\d+)\.00', line)
        if qty_matches:
            # Found potential quantity line, look for dock date in the same line or nearby
            potential_qty = int(qty_matches[0])
            
            # Look for dock date in the same line first
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
            if date_match:
                # Validate this looks like a dock date (not an order date from header)
                found_date = date_match.group(1)
                # Skip dates that are clearly order dates (usually in header)
                if not any(header_word in lines[max(0, i-2):i+1] for header_word in ['ORDER', 'PURCHASE', 'PO']):
                    quantity = potential_qty
                    dock_date = found_date
                    break
            
            # If no date in same line, check nearby lines (within 3 lines)
            if not dock_date:
                search_range = range(max(0, i - 2), min(len(lines), i + 3))
                for j in search_range:
                    if j != i:  # Don't re-check the same line
                        nearby_line = lines[j]
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', nearby_line)
                        if date_match:
                            found_date = date_match.group(1)
                            # Additional validation: dock dates are usually future dates
                            try:
                                date_obj = datetime.strptime(found_date, '%m/%d/%Y')
                                current_date = datetime.now()
                                # If date is within reasonable range (not too far in past/future)
                                if (date_obj - current_date).days >= -30 and (date_obj - current_date).days <= 365:
                                    quantity = potential_qty
                                    dock_date = found_date
                                    break
                            except:
                                pass
            
            if quantity and dock_date:
                break
    
    # Strategy 2: Fallback - look for quantity patterns separately
    if not quantity:
        # Look for decimal quantities (X.00 format)
        decimal_pattern = r'(\d+)\.00'
        matches = re.findall(decimal_pattern, text)
        if matches:
            for match in matches:
                qty = int(match)
                # Reasonable quantity range
                if 1 <= qty <= 10000:
                    quantity = qty
                    break
    
    # Strategy 3: Fallback - look for dock date separately
    if not dock_date:
        # Find all dates and pick the most likely dock date
        date_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', text)
        for date in date_matches:
            try:
                date_obj = datetime.strptime(date, '%m/%d/%Y')
                current_date = datetime.now()
                # Look for future dates (dock dates are typically future delivery dates)
                if (date_obj - current_date).days >= -7 and (date_obj - current_date).days <= 365:
                    dock_date = date
                    break
            except:
                pass
    
    return quantity, dock_date

def test_extraction():
    """Test the improved extraction function"""
    print("=" * 60)
    print("OCR Extraction Test - PO 4551240889")
    print("=" * 60)
    
    print("Testing with sample OCR text...")
    print("\nOriginal OCR Output:")
    print("  Quantity: 165 (INCORRECT)")
    print("  Dock Date: 09/03/2025")
    
    print("\nRunning improved extraction...")
    quantity, dock_date = extract_quantity_and_dock_date(SAMPLE_OCR_TEXT)
    
    print(f"\nImproved Extraction Results:")
    print(f"  Quantity: {quantity}")
    print(f"  Dock Date: {dock_date}")
    
    print(f"\nExpected Results (from image):")
    print(f"  Quantity: 10 (from '10.00' in table)")
    print(f"  Dock Date: 09/03/2025")
    
    # Check accuracy
    expected_qty = 10
    expected_date = "09/03/2025"
    
    qty_correct = quantity == expected_qty
    date_correct = dock_date == expected_date
    
    print(f"\nAccuracy Check:")
    print(f"  Quantity: {'✅ CORRECT' if qty_correct else '❌ INCORRECT'}")
    print(f"  Dock Date: {'✅ CORRECT' if date_correct else '❌ INCORRECT'}")
    
    if qty_correct and date_correct:
        print(f"\n🎉 SUCCESS: OCR extraction improved!")
    else:
        print(f"\n⚠️  PARTIAL: Some fields still need adjustment")
    
    print("=" * 60)

if __name__ == "__main__":
    test_extraction()

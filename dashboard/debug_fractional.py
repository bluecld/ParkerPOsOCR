#!/usr/bin/env python3

import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

from extract_po_details import extract_quantity_and_dock_date
import re

# Test the problematic fractional quantity case
test_text = """
Item Description                               Unit Price  UM   Dock date   Net amount
3       XYZ789         B         2.50        125.00      LBS     09/15/2025   312.50
"""

print("🔍 DEBUGGING FRACTIONAL QUANTITY CASE")
print("="*80)
print(f"📝 Test text:\n{test_text}")
print("="*80)

# Check what regex patterns match
lines = test_text.strip().split('\n')
for i, line in enumerate(lines):
    print(f"Line {i}: {line}")
    
    # Check for unit indicators
    unit_match = re.search(r'\b(EA|LBS|PCS|EACH|PIECES?)\b', line, re.IGNORECASE)
    print(f"  Unit indicator found: {unit_match.group() if unit_match else 'None'}")
    
    # Check for .00 matches
    decimal_00_matches = re.findall(r'(\d+)\.00\b', line)
    print(f"  .00 matches: {decimal_00_matches}")
    
    # Check line segments
    if unit_match:
        segments = re.split(r'\s{2,}', line.strip())
        print(f"  Segments: {segments}")
        
        for j, segment in enumerate(segments):
            if '.00' in segment:
                segment_matches = re.findall(r'(\d+)\.00\b', segment)
                print(f"    Segment {j} '{segment}': .00 matches = {segment_matches}")
                
                for qty_str in segment_matches:
                    potential_qty = int(qty_str)
                    print(f"      Potential qty: {potential_qty}")
                    print(f"      Range check (1-1000): {1 <= potential_qty <= 1000}")
                    print(f"      Position check (j < len-2): {j} < {len(segments)-2} = {j < len(segments) - 2}")
                    print(f"      Size check (< 500): {potential_qty < 500}")
                    
                    if (1 <= potential_qty <= 1000 and 
                        j < len(segments) - 2 and 
                        potential_qty < 500):
                        print(f"      ❌ WOULD SELECT: {potential_qty}")
                    else:
                        print(f"      ✅ WOULD REJECT: {potential_qty}")

print("\n" + "="*80)
print("🧪 Running actual extraction function:")
quantity, dock_date = extract_quantity_and_dock_date(test_text)
print(f"Result: quantity={quantity}, dock_date={dock_date}")

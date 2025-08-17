#!/usr/bin/env python3

import sys
import os
import re
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

test_line = "3       XYZ789         B         2.50        125.00      LBS     09/15/2025   312.50"

print("🔍 DEBUGGING FRACTIONAL CASE")
print("="*60)
print(f"Line: {test_line}")

# Check for units
unit_match = re.search(r'\b(EA|LBS|PCS|EACH|PIECES?)\b', test_line, re.IGNORECASE)
print(f"Unit found: {unit_match.group() if unit_match else 'None'}")

if unit_match:
    segments = re.split(r'\s{2,}', test_line.strip())
    print(f"Segments: {segments}")
    print(f"Total segments: {len(segments)}")
    print(f"Last two positions: {len(segments)-2} to {len(segments)-1}")
    
    for j, segment in enumerate(segments):
        print(f"Segment {j}: '{segment}'")
        
        # Check if this position is in last two columns
        in_last_two = j >= len(segments) - 2
        print(f"  In last two columns: {in_last_two}")
        
        # Check for fractional values in this segment
        fractional_match = re.search(r'\d+\.(?!00\b)\d{2}', segment)
        print(f"  Has fractional: {fractional_match.group() if fractional_match else 'None'}")
        
        # Check for .00 values
        decimal_00_matches = re.findall(r'(\d+)\.00\b', segment)
        print(f"  .00 matches: {decimal_00_matches}")
        
        if not in_last_two and not fractional_match and decimal_00_matches:
            for qty_str in decimal_00_matches:
                potential_qty = int(qty_str)
                print(f"    Potential qty: {potential_qty}")
                print(f"    Range check (1-1000): {1 <= potential_qty <= 1000}")
                print(f"    Size check (< 500): {potential_qty < 500}")
                
                if (1 <= potential_qty <= 1000 and potential_qty < 500):
                    print(f"    ❌ WOULD SELECT: {potential_qty}")
                else:
                    print(f"    ✅ WOULD REJECT: {potential_qty}")

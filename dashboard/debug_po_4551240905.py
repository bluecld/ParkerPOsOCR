#!/usr/bin/env python3

import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

from extract_po_details import extract_quantity_and_dock_date

# Test with PO 4551240905 text structure
test_text = """
Date
08/19/2025
UM
EA
Quantity
10.00
MILL, ASSEMBLY,
DRILL,
ETC.
4 RIVET
APPLY
PRIMER
PER
NOTE
1. ASSEMBLE
ITEM
2 SPACER,
ITEM
3 BEARING
AND
ITEM
EA
08/19/2025
32.50
"""

print("🔍 DEBUGGING PO 4551240905 QUANTITY EXTRACTION")
print("="*60)
print(f"📝 Text structure:\n{test_text}")
print("="*60)

# Test extraction
quantity, dock_date = extract_quantity_and_dock_date(test_text)
print(f"✅ Result: quantity={quantity}, dock_date={dock_date}")

# Test individual lines
lines = test_text.strip().split('\n')
for i, line in enumerate(lines):
    if 'EA' in line:
        print(f"Line {i}: '{line}' (contains EA)")
        context = lines[max(0,i-2):i+5]
        print(f"Context: {context}")
        print()

#!/usr/bin/env python3

import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

from extract_po_details import extract_quantity_and_dock_date
import re

print("="*80)
print("TESTING QUANTITY vs PRICE DISTINCTION")
print("="*80)

# Test cases
test_cases = [
    {
        "name": "Po 4551240889 Structure",
        "text": "10                                            10.00      16.50        EA  09/03/2025 165.00",
        "expected_qty": 10,
        "expected_date": "09/03/2025",
        "notes": "Should pick 10.00 (quantity) not 16.50 (price) or 165.00 (total)"
    },
    {
        "name": "Similar Case Different Values", 
        "text": "5       ABC123-4       A         25.00       45.75       EA      08/30/2025   1143.75",
        "expected_qty": 25,
        "expected_date": "08/30/2025",
        "notes": "Should pick 25.00 (quantity) not 45.75 (price) or 1143.75 (total)"
    },
    {
        "name": "Fractional Quantity",
        "text": "3       XYZ789         B         2.50        125.00      LBS     09/15/2025   312.50",
        "expected_qty": None,
        "expected_date": "09/15/2025",
        "notes": "Should not extract fractional quantities, only whole numbers ending in .00"
    },
    {
        "name": "Multiple Decimals Line",
        "text": "10    154370-8 OP20 ASSEMBLY    N    10.00    16.50    EA    09/03/2025    165.00",
        "expected_qty": 10,
        "expected_date": "09/03/2025", 
        "notes": "All values on one line - should pick first .00 value as quantity"
    }
]

passed = 0
total = 0

for test in test_cases:
    print(f"\n🧪 Test: {test['name']}")
    print("-" * 60)
    print(f"📝 Notes: {test['notes']}")
    
    # Show what decimals are found
    decimals = re.findall(r'\d+\.\d{2}', test['text'])
    print(f"\n📊 Data line: {test['text']}")
    print(f"💰 All decimals found: {decimals}")
    
    # Run extraction
    qty, date = extract_quantity_and_dock_date(test['text'])
    
    # Check results
    qty_correct = qty == test['expected_qty']
    date_correct = date == test['expected_date']
    
    expected_qty_str = str(test["expected_qty"])
    expected_date_str = str(test["expected_date"])
    
    print(f"\n  {'✅' if qty_correct else '❌'} Quantity: {qty} {'(correct)' if qty_correct else f'(expected {expected_qty_str})'}")
    print(f"  {'✅' if date_correct else '❌'} Dock Date: {date} {'(correct)' if date_correct else f'(expected {expected_date_str})'}")
    
    if qty_correct and date_correct:
        passed += 1
    total += 1

print("\n" + "="*80)
if passed == total:
    print("✅ ALL TESTS PASSED!")
else:
    print(f"⚠️  {passed}/{total} TESTS PASSED")

print("\n💡 KEY INSIGHTS:")
print("• Quantities typically end in .00 (whole numbers)")
print("• Prices can have cents (.XX)")
print("• Quantities appear before prices in table structure") 
print("• Unit indicators (EA, LBS) help identify quantity lines")
print("• Position-based parsing helps with multi-decimal lines")
print("• Lines with fractional decimals are skipped to avoid confusion")
print("="*80)

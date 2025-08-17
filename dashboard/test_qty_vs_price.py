#!/usr/bin/env python3
"""
Test Quantity vs Price Distinction
Test the improved logic to distinguish between quantity and price in table structures
"""

import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

from extract_po_details import extract_quantity_and_dock_date
import re
from datetime import datetime

# Test cases based on the actual PO structure where quantity and price are close
TEST_CASES = {
    "po_4551240889_structure": {
        "text": """
Item    Part number                 Revision  Quantity    Net    Per  UM  Dock date    Net
        description                                       price              amount
10                                            10.00      16.50        EA  09/03/2025 165.00
154370-8 OP20 ASSEMBLY
        """,
        "expected_quantity": 10,
        "expected_dock_date": "09/03/2025",
        "notes": "Should pick 10.00 (quantity) not 16.50 (price) or 165.00 (total)"
    },
    
    "similar_case_different_values": {
        "text": """
Item    Part number    Revision  Quantity    Net price   Per  UM  Dock date    Net amount
5       ABC123-4       A         25.00       45.75       EA      08/30/2025   1143.75
        """,
        "expected_quantity": 25,
        "expected_dock_date": "08/30/2025",
        "notes": "Should pick 25.00 (quantity) not 45.75 (price) or 1143.75 (total)"
    },
    
    "fractional_quantity": {
        "text": """
Item    Part number    Revision  Quantity    Net price   Per  UM  Dock date    Net amount
3       XYZ789         B         2.50        125.00      LBS     09/15/2025   312.50
        """,
        "expected_quantity": None,  # Should not extract 2.50 as it's not whole number
        "expected_dock_date": "09/15/2025",
        "notes": "Should not extract fractional quantities, only whole numbers ending in .00"
    },
    
    "multiple_decimals_line": {
        "text": """
10    154370-8 OP20 ASSEMBLY    N    10.00    16.50    EA    09/03/2025    165.00
        """,
        "expected_quantity": 10,
        "expected_dock_date": "09/03/2025",
        "notes": "All values on one line - should pick first .00 value as quantity"
    }
}

def extract_quantity_and_dock_date(text):
    """Extract quantity as whole number and dock date from the same context"""
    quantity = None
    dock_date = None
    
    lines = text.split('\n')
    
    # Strategy 1: Table-aware extraction - distinguish quantity from price
    for i, line in enumerate(lines):
        # Look for lines that contain both decimal numbers AND unit indicators
        if re.search(r'\b(EA|LBS|PCS|EACH|PIECES?)\b', line, re.IGNORECASE):
            # This line likely contains quantity information
            decimal_matches = re.findall(r'(\d+)\.(\d{2})', line)
            
            for qty_str, cents in decimal_matches:
                potential_qty = int(qty_str)
                decimal_part = int(cents)
                
                # Quantity logic: Usually whole numbers (ends in .00)
                if decimal_part == 0 and 1 <= potential_qty <= 10000:
                    quantity = potential_qty
                    
                    # Look for dock date in the same line
                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                    if date_match:
                        dock_date = date_match.group(1)
                        break
            
            if quantity:
                break
    
    # Strategy 2: Position-based extraction if Strategy 1 fails
    if not quantity:
        for i, line in enumerate(lines):
            decimal_matches = re.findall(r'(\d+)\.(\d{2})', line)
            
            if len(decimal_matches) >= 2:
                # Multiple decimals found - parse by position
                segments = re.split(r'\s{2,}', line.strip())
                
                for j, segment in enumerate(segments):
                    segment_decimals = re.findall(r'(\d+)\.(\d{2})', segment)
                    
                    for qty_str, cents in segment_decimals:
                        potential_qty = int(qty_str)
                        decimal_part = int(cents)
                        
                        if (decimal_part == 0 and 
                            1 <= potential_qty <= 1000 and 
                            j < len(segments) - 2):
                            
                            quantity = potential_qty
                            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                            if date_match:
                                dock_date = date_match.group(1)
                            break
                    
                    if quantity:
                        break
                
                if quantity:
                    break
    
    # Strategy 3: Context-aware fallback
    if not quantity:
        for i, line in enumerate(lines):
            if re.search(r'\b\d{5,6}-\d+\b', line):  # Part number pattern
                decimal_matches = re.findall(r'(\d+)\.00', line)
                
                for match in decimal_matches:
                    potential_qty = int(match)
                    if 1 <= potential_qty <= 500:
                        quantity = potential_qty
                        
                        context_lines = lines[max(0, i-1):i+3]
                        for context_line in context_lines:
                            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', context_line)
                            if date_match:
                                dock_date = date_match.group(1)
                                break
                        break
                
                if quantity:
                    break
    
    # Strategy 4: Date extraction if not found
    if quantity and not dock_date:
        date_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', text)
        for date in date_matches:
            try:
                date_obj = datetime.strptime(date, '%m/%d/%Y')
                current_date = datetime.now()
                if (date_obj - current_date).days >= -7 and (date_obj - current_date).days <= 365:
                    dock_date = date
                    break
            except:
                pass
    
    return quantity, dock_date

def test_quantity_price_distinction():
    """Test the improved quantity vs price extraction"""
    
    print("=" * 80)
    print("TESTING QUANTITY vs PRICE DISTINCTION")
    print("=" * 80)
    
    all_passed = True
    
    for test_name, test_data in TEST_CASES.items():
        print(f"\n🧪 Test: {test_name.replace('_', ' ').title()}")
        print("-" * 60)
        print(f"📝 Notes: {test_data['notes']}")
        print()
        
        text = test_data["text"]
        expected_qty = test_data["expected_quantity"]
        expected_date = test_data["expected_dock_date"]
        
        # Extract values
        actual_qty, actual_date = extract_quantity_and_dock_date(text)
        
        # Show the line being analyzed
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        data_line = [line for line in lines if any(char.isdigit() for char in line)]
        if data_line:
            print(f"📊 Data line: {data_line[0]}")
            # Show all decimal numbers found
            decimals = re.findall(r'(\d+\.\d{2})', data_line[0])
            print(f"💰 All decimals found: {decimals}")
        print()
        
        # Test quantity
        if actual_qty == expected_qty:
            print(f"  ✅ Quantity: {actual_qty} (correct)")
        else:
            print(f"  ❌ Quantity: Expected {expected_qty}, got {actual_qty}")
            all_passed = False
        
        # Test dock date
        if actual_date == expected_date:
            print(f"  ✅ Dock Date: {actual_date} (correct)")
        else:
            print(f"  ❌ Dock Date: Expected {expected_date}, got {actual_date}")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Quantity vs Price distinction working!")
    else:
        print("⚠️  SOME TESTS FAILED - Logic needs refinement")
    
    print("\n💡 KEY INSIGHTS:")
    print("• Quantities typically end in .00 (whole numbers)")
    print("• Prices can have cents (.XX)")
    print("• Quantities appear before prices in table structure")
    print("• Unit indicators (EA, LBS) help identify quantity lines")
    print("• Position-based parsing helps with multi-decimal lines")
    print("=" * 80)

if __name__ == "__main__":
    test_quantity_price_distinction()

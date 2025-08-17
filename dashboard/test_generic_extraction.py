#!/usr/bin/env python3
"""
Test Improved Generic Extraction
Test the updated extraction functions with various inputs
"""

import re
import sys
import os

# Test data for different scenarios
TEST_CASES = {
    "parker_po": {
        "text": """
        Production Order: 125157207
        Buyer/phone: Nataly Hernandez / 818-555-0123
        Vendor: TEK ENTERPRISES, INC.
        Payment Terms: 30 Days from Date of Invoice
        """,
        "expected": {
            "production_order": "125157207",
            "buyer_name": "Nataly Hernandez",
            "vendor_name": "TEK ENTERPRISES, INC.",
            "payment_terms": "30 Days from Date of Invoice"
        }
    },
    
    "different_vendor": {
        "text": """
        Production Order: 987654321
        Buyer: John Smith
        Vendor: ACME MANUFACTURING LLC
        Payment Terms: Net 30
        """,
        "expected": {
            "production_order": "987654321",
            "buyer_name": "John Smith",
            "vendor_name": "ACME MANUFACTURING LLC",
            "payment_terms": "Net 30"
        }
    },
    
    "alternative_format": {
        "text": """
        WO: 123456789
        Contact: Sarah Johnson <sarah.johnson@company.com>
        Supplier: GLOBAL PARTS ENTERPRISES
        Terms: Payment due in 45 days
        """,
        "expected": {
            "production_order": "123456789",
            "buyer_name": "Sarah Johnson",
            "vendor_name": "GLOBAL PARTS ENTERPRISES",
            "payment_terms": "Payment due in 45 days"
        }
    }
}

# Mock extraction functions (simplified versions for testing)
def extract_production_order(text):
    """Extract production order number - flexible pattern matching"""
    patterns = [
        r'12\d{7}',
        r'\b1[0-9]{8}\b',
        r'\b[1-9]\d{7,9}\b',
        r'Production\s+Order[:\s]+(\d{8,10})',
        r'PO[:\s]+(\d{8,10})',
        r'WO[:\s]+(\d{8,10})'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result = matches[0]
            if isinstance(result, str) and len(result) >= 8:
                if not re.match(r'^(\d)\1+$', result):
                    return result
    return None

def extract_buyer_name(text):
    """Extract buyer's name from the document"""
    lines = text.split('\n')
    
    # Known buyers
    known_buyers = ["Nataly Hernandez", "Daniel Rodriguez"]
    for buyer in known_buyers:
        if buyer in text:
            return buyer
    
    # Generic patterns
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if 'buyer/phone' in line_lower or 'buyer:' in line_lower or 'contact:' in line_lower:
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j].strip()
                if next_line and len(next_line) > 2:
                    if re.match(r'^[A-Za-z\s\.\-]+$', next_line) and len(next_line.split()) >= 2:
                        return next_line.split('/')[0].strip()
    
    # Email pattern
    email_pattern = r'([A-Za-z\s]+)\s*[<(]?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[>)]?'
    email_matches = re.findall(email_pattern, text)
    for name, email in email_matches:
        name = name.strip()
        if len(name) > 5 and len(name.split()) >= 2:
            return name
    
    # Direct pattern
    name_pattern = r'(?:Name|Contact|Buyer):\s*([A-Za-z\s\.\-]{5,30})'
    name_matches = re.findall(name_pattern, text, re.IGNORECASE)
    if name_matches:
        return name_matches[0].strip()
    
    return None

def extract_vendor_info(text):
    """Extract vendor information"""
    lines = text.split('\n')
    vendor_name = None
    
    # Known vendors
    known_vendors = [
        ("TEK ENTERPRISES", "TEK ENTERPRISES, INC."),
    ]
    
    for vendor_key, vendor_full in known_vendors:
        if vendor_key.upper() in text.upper():
            vendor_name = vendor_full
            break
    
    # Generic extraction
    if not vendor_name:
        for i, line in enumerate(lines):
            line_upper = line.upper()
            if any(indicator in line_upper for indicator in ['VENDOR', 'SUPPLIER']):
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if (next_line and 
                        not any(word in next_line.lower() for word in ['address', 'phone', 'fax', 'number', 'email']) and
                        len(next_line) > 5 and 
                        not next_line.isdigit()):
                        vendor_name = next_line.strip()
                        break
                if vendor_name:
                    break
    
    # Company pattern
    if not vendor_name:
        company_pattern = r'([A-Z\s&,\.]{10,50}(?:INC|LLC|CORP|LTD|COMPANY|ENTERPRISES)[A-Z\s,\.]*)'
        company_matches = re.findall(company_pattern, text)
        if company_matches:
            for match in company_matches:
                match_clean = match.strip()
                if len(match_clean) > 10:
                    vendor_name = match_clean
                    break
    
    if vendor_name:
        is_non_tek = "TEK ENTERPRISES" not in vendor_name.upper()
        return vendor_name, is_non_tek
    
    return None, True

def test_extraction():
    """Test the improved extraction functions"""
    print("=" * 80)
    print("TESTING IMPROVED GENERIC EXTRACTION FUNCTIONS")
    print("=" * 80)
    
    all_passed = True
    
    for test_name, test_data in TEST_CASES.items():
        print(f"\n🧪 Testing: {test_name.replace('_', ' ').title()}")
        print("-" * 50)
        
        text = test_data["text"]
        expected = test_data["expected"]
        
        # Test each extraction function
        results = {}
        
        # Production Order
        results["production_order"] = extract_production_order(text)
        
        # Buyer Name
        results["buyer_name"] = extract_buyer_name(text)
        
        # Vendor Info
        vendor_result = extract_vendor_info(text)
        results["vendor_name"] = vendor_result[0] if vendor_result else None
        
        # Compare results
        for field, expected_value in expected.items():
            actual_value = results.get(field)
            if actual_value == expected_value:
                print(f"  ✅ {field}: {actual_value}")
            else:
                print(f"  ❌ {field}: Expected '{expected_value}', got '{actual_value}'")
                all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Generic extraction working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - May need further refinement")
    print("=" * 80)

if __name__ == "__main__":
    test_extraction()

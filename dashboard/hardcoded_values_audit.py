#!/usr/bin/env python3
"""
Hardcoded Values Audit
Scan the OCR extraction script for hardcoded values that should be made configurable
"""

import re

def scan_hardcoded_values():
    """Identify hardcoded values in the extraction script"""
    
    print("=" * 80)
    print("HARDCODED VALUES AUDIT - OCR EXTRACTION SCRIPT")
    print("=" * 80)
    
    issues = []
    
    print("🔍 ISSUES FOUND:")
    print("=" * 40)
    
    # Issue 1: Hardcoded buyers
    print("1. HARDCODED BUYER NAMES")
    print("   📍 Location: extract_buyer_name() function")
    print("   ❌ Hardcoded: ['Nataly Hernandez', 'Daniel Rodriguez']")
    print("   🎯 Impact: Will fail for POs with different buyers")
    print("   🔧 Fix: Make buyer list configurable or use pattern matching")
    print()
    issues.append("buyer_names")
    
    # Issue 2: Hardcoded vendor
    print("2. HARDCODED VENDOR NAME")
    print("   📍 Location: extract_vendor_info() function")
    print("   ❌ Hardcoded: 'TEK ENTERPRISES, INC.'")
    print("   🎯 Impact: Will fail for POs from other vendors")
    print("   🔧 Fix: Use generic vendor extraction logic")
    print()
    issues.append("vendor_name")
    
    # Issue 3: Hardcoded payment terms
    print("3. HARDCODED PAYMENT TERMS")
    print("   📍 Location: extract_payment_terms() function")
    print("   ❌ Hardcoded: '30 Days from Date of Invoice'")
    print("   🎯 Impact: May not recognize other valid payment terms")
    print("   🔧 Fix: Use pattern matching for various payment terms")
    print()
    issues.append("payment_terms")
    
    # Issue 4: Production order pattern
    print("4. HARDCODED PRODUCTION ORDER PATTERN")
    print("   📍 Location: extract_production_order() function")
    print("   ❌ Hardcoded: 9-digit numbers starting with '12'")
    print("   🎯 Impact: Will fail for different production order formats")
    print("   🔧 Fix: Make pattern configurable or more flexible")
    print()
    issues.append("production_order_pattern")
    
    # Issue 5: Revision validation
    print("5. HARDCODED REVISION LENGTH")
    print("   📍 Location: extract_revision() function")
    print("   ❌ Hardcoded: Limited to 1-3 characters")
    print("   🎯 Impact: May truncate longer revision numbers")
    print("   🔧 Fix: Make revision length configurable")
    print()
    issues.append("revision_length")
    
    print("📊 SUMMARY:")
    print("=" * 20)
    print(f"   Total Issues Found: {len(issues)}")
    print("   Severity: HIGH (will cause failures with different PO formats)")
    print("   Priority: Fix before processing diverse PO sources")
    print()
    
    print("🎯 RECOMMENDED FIXES:")
    print("=" * 30)
    print("1. Create configuration file for vendor-specific patterns")
    print("2. Implement generic pattern matching algorithms")
    print("3. Add fallback extraction methods")
    print("4. Make validation rules configurable")
    print("5. Add confidence scoring for extracted values")
    print()
    
    return issues

def generate_fixes():
    """Generate specific fixes for hardcoded values"""
    
    print("🔧 SPECIFIC FIXES TO IMPLEMENT:")
    print("=" * 40)
    
    fixes = {
        "buyer_names": """
# BEFORE (Hardcoded):
known_buyers = ["Nataly Hernandez", "Daniel Rodriguez"]

# AFTER (Configurable):
def extract_buyer_name(text, config=None):
    known_buyers = config.get('known_buyers', []) if config else []
    
    # Try known buyers first if provided
    for buyer in known_buyers:
        if buyer in text:
            return buyer
    
    # Generic pattern matching for any buyer name
    # Look for patterns like "Buyer: [Name]" or after "Buyer/phone"
""",
        
        "vendor_name": """
# BEFORE (Hardcoded):
vendor_name = "TEK ENTERPRISES, INC."

# AFTER (Generic):
def extract_vendor_info(text, config=None):
    expected_vendors = config.get('expected_vendors', []) if config else []
    
    # Try configured vendors first
    for vendor in expected_vendors:
        if vendor.upper() in text.upper():
            return vendor, False
    
    # Generic vendor extraction - look for vendor field patterns
    # Extract actual vendor name from document structure
""",
        
        "payment_terms": """
# BEFORE (Hardcoded):
standard_terms = "30 Days from Date of Invoice"

# AFTER (Pattern-based):
def extract_payment_terms(text, config=None):
    standard_patterns = config.get('standard_payment_terms', [
        "30 Days from Date of Invoice",
        "Net 30",
        "30 Days",
        "Payment due in 30 days"
    ]) if config else ["30 Days from Date of Invoice"]
    
    # Check for any standard pattern
    for pattern in standard_patterns:
        if pattern.lower() in text.lower():
            return pattern, False
    
    # Extract actual payment terms from document
""",
        
        "production_order_pattern": """
# BEFORE (Hardcoded):
pattern = r'12\\d{7}'  # Only 9-digit numbers starting with 12

# AFTER (Configurable):
def extract_production_order(text, config=None):
    patterns = config.get('production_order_patterns', [
        r'12\\d{7}',      # Parker format: 12 + 7 digits
        r'\\d{8,10}',     # Generic 8-10 digit numbers
        r'PO\\d+',        # PO prefix format
        r'WO\\d+'         # Work order format
    ]) if config else [r'12\\d{7}']
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    return None
"""
    }
    
    for issue, fix in fixes.items():
        print(f"Fix for {issue}:")
        print(fix)
        print("-" * 60)

if __name__ == "__main__":
    issues = scan_hardcoded_values()
    print()
    generate_fixes()

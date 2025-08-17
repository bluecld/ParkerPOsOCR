#!/usr/bin/env python3

import sys
import os
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

# Import the extraction functions
from extract_po_details import extract_text_from_pdf, extract_production_order, extract_part_number

def test_part_extraction(pdf_path):
    print(f"Testing part number extraction on: {pdf_path}")
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Get production order
    production_order = extract_production_order(text)
    print(f"Production Order: {production_order}")
    
    # Test improved part number extraction
    part_number = extract_part_number(text, production_order)
    print(f"Extracted Part Number: {part_number}")
    
    # Also search for any OP patterns in the text for debugging
    import re
    op_matches = re.findall(r'[Oo]p\d+', text, re.IGNORECASE)
    print(f"OP patterns found in document: {op_matches}")
    
    return part_number

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_extraction.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_part_extraction(pdf_path)

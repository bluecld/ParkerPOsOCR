"""
Extract Purchase Order Information and Split PDF
"""

import fitz
import pytesseract
from PIL import Image
import io
import re
import json
import os

# Use system tesseract (container has it installed)

def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF using OCR"""
    doc = fitz.open(pdf_path)
    all_text = ""
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Try to extract text directly first
        page_text = page.get_text()
        
        # If no text found, use OCR
        if not page_text.strip():
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            page_text = pytesseract.image_to_string(img)
        
        all_text += f"PAGE {page_num + 1}:\n{page_text}\n\n"
    
    doc.close()
    return all_text

def extract_po_number(text):
    """Extract 10-digit purchase order number starting with 455"""
    # Look for 455 followed by 7 more digits
    pattern = r'455\d{7}'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def extract_page_count(text):
    """Extract page count from 'Page X of Y' format with OCR error handling"""
    # Try multiple patterns to handle OCR and font artifacts
    patterns = [
        r'Page\s+\d+\s+of\s+(\d+)',        # Standard: "Page 1 of 2"
        r'Page\s+[l1!itI]?\s*of\s*(\d+)',   # OCR errors for the X value
        r'Page\s+\S+\s+of\s+(\d+)',        # Any token for X (e.g., 'tof')
        r'[l1!itI]\s*of\s*(\d+)',           # Minimal: "lof 2" or "1of 2"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take the first reasonable page count (1-200 pages)
            for match in matches:
                try:
                    count = int(match)
                    if 1 <= count <= 200:
                        return count
                except ValueError:
                    continue
    return None

def create_po_folder(po_number):
    """Create folder with PO number name"""
    folder_path = os.path.join(os.getcwd(), po_number)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def split_pdf(input_pdf, po_number, page_count, output_folder):
    """Split PDF into PO section and Router section"""
    doc = fitz.open(input_pdf)
    total_pages = len(doc)
    
    # Create PO document (first 'page_count' pages)
    po_doc = fitz.open()
    for page_num in range(min(page_count, total_pages)):
        po_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
    
    po_filename = f"PO_{po_number}.pdf"
    po_path = os.path.join(output_folder, po_filename)
    po_doc.save(po_path)
    po_doc.close()
    
    # Create Router document (remaining pages)
    if total_pages > page_count:
        router_doc = fitz.open()
        for page_num in range(page_count, total_pages):
            router_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        router_filename = f"Router_{po_number}.pdf"
        router_path = os.path.join(output_folder, router_filename)
        router_doc.save(router_path)
        router_doc.close()
    else:
        router_path = None
    
    doc.close()
    return po_path, router_path

def main():
    # Get searchable PDF name from environment variable or use default
    input_pdf = os.environ.get("SEARCHABLE_PDF", "final_searchable_output.pdf")
    
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(input_pdf)
    
    print("Extracting purchase order number...")
    po_number = extract_po_number(text)
    
    print("Extracting page count...")
    page_count = extract_page_count(text)
    
    if not po_number:
        print("Could not find purchase order number starting with 455")
        import sys as _sys
        _sys.exit(1)
    
    if not page_count:
        print("Could not find page count information")
        import sys as _sys
        _sys.exit(1)
    
    print(f"Found PO Number: {po_number}")
    print(f"Found Page Count: {page_count}")
    
    # Create JSON with extracted information
    po_info = {
        "purchase_order_number": po_number,
        "page_count": page_count,
        "source_file": input_pdf
    }
    
    # Create folder
    output_folder = create_po_folder(po_number)
    
    # Save JSON file
    json_path = os.path.join(output_folder, f"{po_number}_info.json")
    with open(json_path, 'w') as f:
        json.dump(po_info, f, indent=2)
    
    print(f"Created folder: {output_folder}")
    print(f"Saved JSON info: {json_path}")
    
    # Split PDF
    print("Splitting PDF...")
    po_path, router_path = split_pdf(input_pdf, po_number, page_count, output_folder)
    
    print(f"Created PO file: {po_path}")
    if router_path:
        print(f"Created Router file: {router_path}")
    else:
        print("No additional pages for Router file")

if __name__ == "__main__":
    main()
"""
Extract detailed information from PO PDF file
"""

import fitz
import pytesseract
from PIL import Image
import io
import re
import json
import os

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF using OCR with better accuracy"""
    doc = fitz.open(pdf_path)
    all_text = ""
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Try to extract text directly first
        page_text = page.get_text()
        
        # If no text found or minimal text, use OCR
        if len(page_text.strip()) < 50:
            # Use adaptive resolution based on source quality
            # For 300dpi scans, use higher scaling; for 600dpi, moderate scaling
            matrices = [
                fitz.Matrix(4, 4),  # Higher res for 300dpi scans
                fitz.Matrix(3, 3),  # Standard high res
                fitz.Matrix(2, 2)   # Lower res for already high-quality scans
            ]
            
            best_text = ""
            best_length = 0
            
            for matrix in matrices:
                try:
                    pix = page.get_pixmap(matrix=matrix)
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data)).convert('L')
                    
                    # Enhanced OCR configs for different scan qualities
                    configs = [
                        r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/-*().,: ',
                        r'--oem 3 --psm 4',
                        r'--oem 3 --psm 3',
                        r'--oem 1 --psm 6',  # Legacy engine for difficult scans
                        r'--oem 2 --psm 6'   # Cube engine
                    ]
                    
                    for config in configs:
                        try:
                            ocr_text = pytesseract.image_to_string(img, config=config)
                            if len(ocr_text) > best_length:
                                best_text = ocr_text
                                best_length = len(ocr_text)
                        except:
                            continue
                    
                    # If we got decent results, don't try more matrices
                    if best_length > 200:
                        break
                        
                except Exception as e:
                    print(f"OCR matrix {matrix} failed: {e}")
                    continue
            
            page_text = best_text if best_text else page_text
        
        all_text += f"PAGE {page_num + 1}:\n{page_text}\n\n"
    
    doc.close()
    return all_text

def extract_production_order(text):
    """Extract production order number - flexible pattern matching"""
    # Multiple patterns to try, in order of preference
    patterns = [
        r'12\d{7}',           # Parker format: 12 followed by 7 digits (125157207)
        r'\b1[0-9]{8}\b',     # 9-digit numbers starting with 1
        r'\b[1-9]\d{7,9}\b',  # 8-10 digit numbers starting with non-zero
        r'Production\s+Order[:\s]+(\d{8,10})',  # "Production Order: NNNNNN"
        r'PO[:\s]+(\d{8,10})', # "PO: NNNNNN"
        r'WO[:\s]+(\d{8,10})'  # "WO: NNNNNN" (Work Order)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Return the first match, handling both direct matches and group captures
            result = matches[0]
            # Validate the number looks reasonable (not too many repeated digits)
            if isinstance(result, str) and len(result) >= 8:
                # Check for obviously invalid patterns (all same digit, etc.)
                if not re.match(r'^(\d)\1+$', result):  # Not all same digit
                    return result
    
    return None

def extract_revision(text):
    """Extract revision number following 'REV' - clean to 1-3 characters"""
    # Look for REV followed by alphanumeric characters
    pattern = r'REV\s*([A-Z0-9]+)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        revision = matches[0]
        # Clean up revision - take only first 1-3 alphanumeric characters
        clean_revision = re.match(r'^([A-Z0-9]{1,3})', revision.upper())
        if clean_revision:
            return clean_revision.group(1)
        else:
            # Fallback - take first character if it's alphanumeric
            if revision and revision[0].isalnum():
                return revision[0].upper()
    return None

def extract_part_number(text, production_order):
    """Extract part number from line above Production Order"""
    if not production_order:
        return None
    
    lines = text.split('\n')
    
    # Look for production order and then search nearby lines for part number
    for i, line in enumerate(lines):
        if production_order in line:
            # Search in a wider context around the production order
            start_idx = max(0, i-10)
            end_idx = min(len(lines), i+5)
            context_lines = lines[start_idx:end_idx]
            
            # Pattern 1: Look for digit-digit (like 157710-30) with Op pattern (may be on separate lines)
            for j, context_line in enumerate(context_lines):
                # Look for digits-digits pattern with Op on same line
                dash_pattern_match = re.search(r'(\d+[-_]\d+)\s*[*]?([Oo]p\d+)', context_line, re.IGNORECASE)
                if dash_pattern_match:
                    part_base = dash_pattern_match.group(1)
                    op_part = dash_pattern_match.group(2).upper()  # Keep original case for OP
                    return f"{part_base}*{op_part}"
                
                # Look for digits-digits pattern that might have Op on next line or nearby
                dash_match = re.search(r'(\d+[-_]\d+)', context_line)
                if dash_match:
                    part_base = dash_match.group(1)
                    
                    # Search in multiple subsequent lines for OP pattern
                    for k in range(j+1, min(j+5, len(context_lines))):
                        if k < len(context_lines):
                            search_line = context_lines[k]
                            op_match = re.search(r'[*]?([Oo]p\d+)', search_line, re.IGNORECASE)
                            if op_match:
                                op_part = op_match.group(1).upper()
                                return f"{part_base}*{op_part}"
                    
                    # If no OP found, also search in the broader context around this part number
                    context_text = ' '.join(context_lines[max(0, j-3):min(len(context_lines), j+8)])
                    op_match = re.search(rf'{re.escape(part_base)}.*?([Oo]p\d+)', context_text, re.IGNORECASE)
                    if op_match:
                        op_part = op_match.group(1).upper()
                        return f"{part_base}*{op_part}"
                    
                    # Store this as a candidate in case we don't find anything better
                    candidate_part = part_base
            
            # Pattern 2: Look for just digits (like 521350) near production order
            for j, context_line in enumerate(context_lines):
                # Look for 6-digit numbers that appear before Op or near production order
                digit_matches = re.findall(r'\b(\d{6})\b', context_line)
                for digit_match in digit_matches:
                    # Check if this appears near an Op pattern
                    context_text = ' '.join(context_lines)
                    if re.search(rf'{digit_match}.*?[Oo]p\d+', context_text, re.IGNORECASE):
                        # Find the Op number
                        op_match = re.search(rf'{digit_match}.*?([Oo]p\d+)', context_text, re.IGNORECASE)
                        if op_match:
                            op_part = op_match.group(1).lower()
                            return f"{digit_match}*{op_part}"
                        else:
                            return digit_match
            
            # Pattern 3: Look for dash patterns without Op, but search harder for OP
            candidate_part = None
            for j, context_line in enumerate(context_lines):
                dash_matches = re.findall(r'(\d+[-_]\d+)', context_line)
                if dash_matches:
                    candidate_part = dash_matches[-1]  # Take the last/closest one to production order
                    
                    # Search the entire context for an OP that might go with this part
                    full_context = ' '.join(context_lines)
                    # Look for OP20, OP30, etc. anywhere in the context
                    op_matches = re.findall(r'[Oo]p\d+', full_context, re.IGNORECASE)
                    if op_matches:
                        # Take the first OP found (most likely to be associated)
                        op_part = op_matches[0].upper()
                        return f"{candidate_part}*{op_part}"
                    else:
                        # Return the part without OP for now, but keep looking
                        break
            
            # If we found a candidate part but no OP, add default *OP20
            if candidate_part:
                return f"{candidate_part}*OP20"
            
            # Pattern 4: Look for standalone numbers near production order
            for j, context_line in enumerate(context_lines):
                if j < len(context_lines) - 2:  # Not the production order line itself
                    standalone_matches = re.findall(r'\b(\d{5,7})\b', context_line)
                    for match in standalone_matches:
                        # Skip obvious non-part numbers (production orders start with 12)
                        if not match.startswith('12') and not match.startswith('455'):
                            return match
            
            break  # Found production order, stop looking
    
    return None

def extract_quantity_and_dock_date(text):
    """Extract quantity as whole number and dock date from the same context"""
    quantity = None
    dock_date = None
    
    lines = text.split('\n')
    
    # Strategy 1: Smart context-aware extraction
    # Look for lines with item/part/revision/quantity/unit/dock date context
    for i, line in enumerate(lines):
        # Look for lines with units and at least one number
        if re.search(r'\b(EA|LBS|PCS|EACH|PIECES?)\b', line, re.IGNORECASE) and re.search(r'\d', line):
            # Try to find header context in previous lines
            header_context = None
            for h in range(max(0, i-3), i):
                if re.search(r'Item.*Quantity.*UM.*Dock', lines[h], re.IGNORECASE):
                    header_context = lines[h]
                    break
            segments = re.split(r'\s+', line.strip())
            # Find the unit position
            unit_idx = None
            for idx, seg in enumerate(segments):
                if re.search(r'\b(EA|LBS|PCS|EACH|PIECES?)\b', seg, re.IGNORECASE):
                    unit_idx = idx
                    break
            # Look for a number (integer or .00) before the unit
            if unit_idx is not None:
                for pos in range(max(0, unit_idx-3), unit_idx):
                    seg = segments[pos]
                    # Accept .00 or integer
                    match = re.match(r'^(\d+)\.00$', seg)
                    if match:
                        val = int(match.group(1))
                        if 1 <= val <= 1000:
                            quantity = val
                            break
                    else:
                        match = re.match(r'^(\d+)$', seg)
                        if match:
                            val = int(match.group(1))
                            if 1 <= val <= 1000:
                                quantity = val
                                break
            # Look for dock date in the same line
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
            if date_match:
                dock_date = date_match.group(1)
            if quantity:
                break
    
    # Strategy 2: Vertical table format - EA on separate lines
    # Look for pattern: "EA" followed by "Quantity" followed by decimal number
    if not quantity:
        for i, line in enumerate(lines):
            # Look for unit indicators in their own line
            if re.match(r'^\s*(EA|LBS|PCS|EACH|PIECES?)\s*$', line, re.IGNORECASE):
                # Check the next few lines for "Quantity" keyword and decimal
                for offset in range(1, 5):  # Check next 4 lines
                    if i + offset < len(lines):
                        next_line = lines[i + offset].strip()
                        
                        # Look for "Quantity" indicator
                        if re.search(r'\bQuantity\b', next_line, re.IGNORECASE):
                            # Check lines after "Quantity" for decimal numbers
                            for qty_offset in range(1, 3):  # Check next 2 lines after "Quantity"
                                if i + offset + qty_offset < len(lines):
                                    qty_line = lines[i + offset + qty_offset].strip()
                                    
                                    # Look for .00 decimal (whole number quantity)
                                    qty_match = re.match(r'^\s*(\d+)\.00\s*$', qty_line)
                                    if qty_match:
                                        potential_qty = int(qty_match.group(1))
                                        if 1 <= potential_qty <= 1000:
                                            quantity = potential_qty
                                            
                                            # Look for date in surrounding context
                                            context_lines = lines[max(0, i-3):i+8]
                                            for context_line in context_lines:
                                                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', context_line)
                                                if date_match:
                                                    dock_date = date_match.group(1)
                                                    break
                                            break
                            if quantity:
                                break
                        
                        # Also check if the line directly contains a .00 decimal 
                        # (case where "Quantity" label might be missing)
                        direct_qty_match = re.match(r'^\s*(\d+)\.00\s*$', next_line)
                        if direct_qty_match:
                            potential_qty = int(direct_qty_match.group(1))
                            if 1 <= potential_qty <= 1000:
                                quantity = potential_qty
                                
                                # Look for date in surrounding context
                                context_lines = lines[max(0, i-3):i+8]
                                for context_line in context_lines:
                                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', context_line)
                                    if date_match:
                                        dock_date = date_match.group(1)
                                        break
                                break
                
                if quantity:
                    break
    
    # Strategy 3: Context-based extraction for part number lines
    if not quantity:
        for i, line in enumerate(lines):
            # Look for lines that contain part numbers (likely detail lines)
            if re.search(r'\b\d{5,6}-\d+\b', line):  # Part number pattern like 154370-8
                # This line likely contains item details including quantity
                
                # STRICT: Only look for quantities that end in .00
                decimal_matches = re.findall(r'(\d+)\.00\b', line)
                
                # Additional context: look for the smallest reasonable .00 value
                # (quantities are typically smaller than prices)
                valid_quantities = []
                for match in decimal_matches:
                    potential_qty = int(match)
                    if 1 <= potential_qty <= 100:  # Conservative range
                        valid_quantities.append(potential_qty)
                
                if valid_quantities:
                    # Pick the smallest valid quantity (most likely to be actual quantity)
                    quantity = min(valid_quantities)
                    
                    # Look for dock date in context
                    context_lines = lines[max(0, i-1):i+3]
                    for context_line in context_lines:
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', context_line)
                        if date_match:
                            try:
                                from datetime import datetime
                                found_date = date_match.group(1)
                                date_obj = datetime.strptime(found_date, '%m/%d/%Y')
                                current_date = datetime.now()
                                # Future dates are more likely to be dock dates
                                if (date_obj - current_date).days >= -7:
                                    dock_date = found_date
                                    break
                            except:
                                pass
                    break
    
    # Strategy 4: Generic fallback with strict validation
    if not quantity:
        # Look for any .00 values but apply strict filtering
        # Split text into lines and check each line carefully
        for line in lines:
            # Skip header lines and look for data lines
            if re.search(r'\b(EA|LBS|PCS|EACH|PIECES?)\b', line, re.IGNORECASE):
                # This line contains units - likely a data line
                decimal_matches = re.findall(r'(\d+)\.00\b', line)
                
                for match in decimal_matches:
                    potential_qty = int(match)
                    # Very conservative range - typical PO quantities
                    if 1 <= potential_qty <= 50:
                        quantity = potential_qty
                        break
                
                if quantity:
                    break
    
    # Strategy 5: Separate date extraction if not found with quantity
    if not dock_date:
        # Find all dates and pick the most likely dock date
        date_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', text)
        for date in date_matches:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date, '%m/%d/%Y')
                current_date = datetime.now()
                # Look for future dates (dock dates are typically future delivery dates)
                if (date_obj - current_date).days >= -7 and (date_obj - current_date).days <= 365:
                    dock_date = date
                    break
            except:
                pass
    
    return quantity, dock_date

def extract_payment_terms(text):
    """Extract payment terms and return (terms, non_standard_flag)"""
    standard_terms = "30 Days from Date of Invoice"
    
    # The text shows "30 Days from" on one line and "Date" and "of" "Invoice" on subsequent lines
    # Look for this pattern across multiple lines
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        if '30' in line and 'days' in line.lower() and 'from' in line.lower():
            # Found potential start, check next few lines
            combined_text = line
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j].strip()
                if next_line:
                    combined_text += ' ' + next_line
                    # Check if we have the complete standard terms
                    if 'date' in combined_text.lower() and 'invoice' in combined_text.lower():
                        return standard_terms, False
    
    # Look for explicit payment terms section
    payment_pattern = r'Payment\s+terms[:\s]*([^\n]+)'
    match = re.search(payment_pattern, text, re.IGNORECASE)
    if match:
        terms = match.group(1).strip()
        is_non_standard = "30 days from date of invoice" not in terms.lower()
        return terms, is_non_standard
    
    # Look for any mention of payment terms in broader context
    for line in lines:
        if 'payment' in line.lower() and 'terms' in line.lower():
            line_clean = ' '.join(line.split())
            return line_clean, True  # Found but likely non-standard
    
    # Default case - if we found "30 Days from" pattern but incomplete, assume standard
    for line in lines:
        if '30' in line and 'days' in line.lower() and 'from' in line.lower():
            return standard_terms, False  # Assume standard terms
    
    return None, True  # No terms found, flag as non-standard

def extract_vendor_info(text):
    """Extract vendor information and return (vendor_name, non_tek_flag)"""
    lines = text.split('\n')
    vendor_name = None
    
    # Strategy 1: Look for known vendor patterns first
    known_vendors = [
        ("TEK ENTERPRISES", "TEK ENTERPRISES, INC."),
        # Add more vendors as needed
    ]
    
    for vendor_key, vendor_full in known_vendors:
        if vendor_key.upper() in text.upper():
            vendor_name = vendor_full
            break
    
    # Strategy 2: Generic vendor extraction - look for vendor field patterns
    if not vendor_name:
        for i, line in enumerate(lines):
            line_upper = line.upper()
            # Look for vendor section indicators
            if any(indicator in line_upper for indicator in ['VENDOR', 'SUPPLIER', 'FROM:']):
                # Check next few lines for vendor name
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    # Skip obvious non-vendor entries
                    if (next_line and 
                        not any(word in next_line.lower() for word in ['address', 'phone', 'fax', 'number', 'email']) and
                        len(next_line) > 5 and 
                        not next_line.isdigit() and
                        not re.match(r'^\d+\s+(.*)', next_line)):  # Skip address numbers
                        
                        # Clean up the vendor name
                        vendor_name = next_line.strip()
                        # Remove common prefixes/suffixes
                        vendor_name = re.sub(r'^(To:|From:|Ship to:|Bill to:)\s*', '', vendor_name, flags=re.IGNORECASE)
                        break
                if vendor_name:
                    break
    
    # Strategy 3: Look for company patterns (all caps, INC, LLC, etc.)
    if not vendor_name:
        company_pattern = r'([A-Z\s&,\.]{10,50}(?:INC|LLC|CORP|LTD|COMPANY|ENTERPRISES)[A-Z\s,\.]*)'
        company_matches = re.findall(company_pattern, text)
        if company_matches:
            # Filter out obvious non-vendors
            for match in company_matches:
                match_clean = match.strip()
                if (len(match_clean) > 10 and 
                    not any(word in match_clean.lower() for word in ['purchase', 'order', 'agreement', 'terms'])):
                    vendor_name = match_clean
                    break
    
    # Strategy 4: Extract from "confirmed with" or similar patterns
    if not vendor_name:
        confirmed_pattern = r'confirmed\s+with\s+([A-Za-z\s&,\.]+)'
        confirmed_matches = re.findall(confirmed_pattern, text, re.IGNORECASE)
        if confirmed_matches:
            vendor_name = confirmed_matches[0].strip()
    
    if vendor_name:
        # Determine if this is a non-TEK vendor
        is_non_tek = "TEK ENTERPRISES" not in vendor_name.upper()
        return vendor_name, is_non_tek
    
    return None, True  # No vendor found, assume non-TEK
    
    return None, True  # No vendor found, flag as non-standard

def extract_buyer_name(text):
    """Extract buyer's name from the document"""
    lines = text.split('\n')
    
    # First, look for known buyers (configurable list)
    known_buyers = ["Nataly Hernandez", "Daniel Rodriguez"]
    for buyer in known_buyers:
        if buyer in text:
            return buyer

    # Generic approach: Look for buyer name pattern - appears after "Buyer/phone" field
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if 'buyer/phone' in line_lower or 'buyer:' in line_lower or 'buyer' in line_lower:
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j].strip()
                if next_line and len(next_line) > 2:
                    # Avoid picking up fax/email/phone/number
                    if not any(x in next_line.lower() for x in ['fax', 'email', 'phone', 'number']):
                        if re.match(r'^[A-Za-z\s\.\-]+$', next_line) and len(next_line.split()) >= 2:
                            return next_line

    # Alternative: Look for email patterns and extract name before @
    email_pattern = r'([A-Za-z\s]+)\s*[<(]?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[>)]?'
    email_matches = re.findall(email_pattern, text)
    for name, email in email_matches:
        name = name.strip()
        if len(name) > 5 and len(name.split()) >= 2:
            return name

    # Last resort: Look for patterns like "Name: [Person Name]"
    name_pattern = r'(?:Name|Contact|Buyer):\s*([A-Za-z\s\.\-]{5,30})'
    name_matches = re.findall(name_pattern, text, re.IGNORECASE)
    if name_matches:
        return name_matches[0].strip()

    # Look for any proper name pattern that appears multiple times (likely buyer name)
    name_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)'
    matches = re.findall(name_pattern, text)
    if matches:
        name_counts = {}
        for match in matches:
            match_lower = match.lower()
            if not any(word in match_lower for word in ['street', 'avenue', 'road', 'drive', 'california', 'hollywood', 'north', 'meggitt', 'enterprises', 'currency', 'buyer']):
                name_counts[match] = name_counts.get(match, 0) + 1
        if name_counts:
            return max(name_counts, key=name_counts.get)

    return None

def extract_dpas_ratings(text):
    """Extract DPAS ratings from the document"""
    dpas_ratings = []
    
    # Look for DPAS Rating: followed by the ratings
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if 'DPAS' in line_upper and 'RATING' in line_upper:
            # Check the same line and next few lines for ratings
            search_text = line
            for j in range(i + 1, min(i + 3, len(lines))):
                search_text += ' ' + lines[j]
            
            # Look for DOA and DOC patterns followed by numbers
            ratings = re.findall(r'(DO[AC]\d+)', search_text.upper())
            dpas_ratings.extend(ratings)
            break
    
    # If not found in structured way, search more broadly
    if not dpas_ratings:
        # Look for DOA/DOC patterns anywhere in text
        all_ratings = re.findall(r'(DO[AC]\d+)', text.upper())
        dpas_ratings.extend(all_ratings)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ratings = []
    for rating in dpas_ratings:
        if rating not in seen:
            seen.add(rating)
            unique_ratings.append(rating)
    
    return unique_ratings if unique_ratings else None

def extract_quality_clauses(text):
    """Extract Quality Clauses (Q numbers with descriptions) from the document"""
    quality_clauses = {}
    
    # Define known quality clauses and their complete descriptions based on the text
    known_clauses = {
        'Q1': 'QUALITY SYSTEMS REQUIREMENTS',
        'Q2': 'SURVEILLANCE BY MEGGITT AND RIGHT OF ENTRY',
        'Q5': 'CERTIFICATION OF CONFORMANCE AND RECORD RETENTION',
        'Q9': 'CORRECTIVE ACTION',
        'Q11': 'SPECIAL PROCESS SOURCES REQUIRED',
        'Q13': 'REPORT OF DISCREPANCY # Quality Notification (QN)',
        'Q14': 'FOREIGN OBJECT DAMAGE (FOD)',
        'Q15': 'ANTI-TERRORIST POLICY',
        'Q26': 'PACKING FOR SHIPMENT',
        'Q32': 'FLOWDOWN OF REQUIREMENTS [QUALITY AND ENVIRONMENTAL]',
        'Q33': 'FAR and DOD FAR SUPPLEMENTAL FLOWDOWN PROVISIONS'
    }
    
    # Extract Q numbers that actually appear in the text
    q_numbers_found = re.findall(r'(Q\d+)', text.upper())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_q_numbers = []
    for q in q_numbers_found:
        if q not in seen:
            seen.add(q)
            unique_q_numbers.append(q)
    
    # Map found Q numbers to their descriptions
    for q_number in unique_q_numbers:
        if q_number in known_clauses:
            quality_clauses[q_number] = known_clauses[q_number]
        else:
            # For unknown Q numbers, try to extract description from context
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if q_number in line.upper():
                    # Try to get description from same line or following lines
                    description_parts = []
                    remaining = line.split(q_number, 1)
                    if len(remaining) > 1:
                        desc = remaining[1].strip()
                        if desc:
                            description_parts.append(desc)
                    
                    # Look at next couple lines for continuation
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not re.match(r'^Q\d+', next_line.upper()) and len(next_line) < 60:
                            description_parts.append(next_line)
                        else:
                            break
                    
                    if description_parts:
                        quality_clauses[q_number] = ' '.join(description_parts).strip()
                    break
    
    return quality_clauses if quality_clauses else None

def main():
    # Find the most recent PO folder (starts with 455)
    po_folders = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('455')]
    if not po_folders:
        print("No PO folders found")
        return
    
    # Get the most recently modified PO folder
    po_folder = max(po_folders, key=lambda d: os.path.getmtime(d))
    po_number = po_folder
    po_file = os.path.join(po_folder, f"PO_{po_number}.pdf")
    json_file = os.path.join(po_folder, f"{po_number}_info.json")
    
    if not os.path.exists(po_file):
        print(f"PO file not found: {po_file}")
        return
    
    print("Extracting detailed text from PO file...")
    text = extract_text_from_pdf(po_file)
    
    print("\\nExtracting Production Order...")
    production_order = extract_production_order(text)
    print(f"Production Order: {production_order}")
    
    print("\\nExtracting Revision...")
    revision = extract_revision(text)
    print(f"Revision: {revision}")
    
    print("\\nExtracting Part Number...")
    part_number = extract_part_number(text, production_order)
    print(f"Part Number: {part_number}")
    
    print("\\nExtracting Quantity and Dock Date...")
    quantity, dock_date = extract_quantity_and_dock_date(text)
    print(f"Quantity: {quantity}")
    print(f"Dock Date: {dock_date}")
    
    print("\\nExtracting Payment Terms...")
    payment_terms, payment_terms_flag = extract_payment_terms(text)
    print(f"Payment Terms: {payment_terms}")
    print(f"Non-standard Payment Terms Flag: {payment_terms_flag}")
    
    print("\\nExtracting Vendor Information...")
    vendor_name, vendor_flag = extract_vendor_info(text)
    print(f"Vendor: {vendor_name}")
    print(f"Non-Tek Vendor Flag: {vendor_flag}")
    
    print("\\nExtracting Buyer Name...")
    buyer_name = extract_buyer_name(text)
    print(f"Buyer: {buyer_name}")
    
    print("\\nExtracting DPAS Ratings...")
    dpas_ratings = extract_dpas_ratings(text)
    print(f"DPAS Ratings: {dpas_ratings}")
    
    print("\\nExtracting Quality Clauses...")
    quality_clauses = extract_quality_clauses(text)
    print(f"Quality Clauses: {quality_clauses}")
    
    # Load existing JSON
    with open(json_file, 'r') as f:
        po_info = json.load(f)
    
    # Add new information
    po_info.update({
        "production_order": production_order,
        "revision": revision,
        "part_number": part_number,
        "quantity": quantity,
        "dock_date": dock_date,
        "payment_terms": payment_terms,
        "payment_terms_non_standard_flag": payment_terms_flag,
        "vendor_name": vendor_name,
        "vendor_non_tek_flag": vendor_flag,
        "buyer_name": buyer_name,
        "dpas_ratings": dpas_ratings,
        "quality_clauses": quality_clauses
    })
    
    # Save updated JSON
    with open(json_file, 'w') as f:
        json.dump(po_info, f, indent=2)
    
    print(f"\\nUpdated JSON file: {json_file}")
    print("\\nExtracted information:")
    print(json.dumps(po_info, indent=2))
    
    # Also save extracted text for debugging
    debug_file = os.path.join(po_folder, "extracted_text.txt")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"\\nSaved extracted text to: {debug_file}")
    
    # Move original searchable PDF to PO folder for complete organization
    original_pdf = po_info.get("source_file", "final_searchable_output.pdf")
    if os.path.exists(original_pdf):
        import shutil
        destination = os.path.join(po_folder, os.path.basename(original_pdf))
        try:
            shutil.move(original_pdf, destination)
            print(f"\\nMoved original PDF to: {destination}")
            # Update JSON to reflect new location
            po_info["source_file"] = os.path.basename(original_pdf)
            with open(json_file, 'w') as f:
                json.dump(po_info, f, indent=2)
        except Exception as e:
            print(f"\\nWarning: Could not move original PDF: {e}")
    else:
        print(f"\\nWarning: Original PDF not found: {original_pdf}")
    
    print(f"\\nComplete processing finished for PO {po_number}")
    print(f"All files organized in folder: {po_folder}")

if __name__ == "__main__":
    main()
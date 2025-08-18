"""
PDF OCR Script - Convert PDFs to searchable PDFs with invisible text overlay

This script uses Tesseract OCR to extract text from PDF pages and creates
a searchable PDF by overlaying invisible text at the correct positions.

Features:
- Automatic page rotation detection and correction
- Advanced image preprocessing for better OCR accuracy
- Multiple OCR configurations to maximize text detection
- Precise text positioning and scaling
- Preserves original visual quality

Requirements:
- PyMuPDF (fitz)
- pytesseract
- OpenCV (cv2)
- PIL/Pillow
- numpy
- Tesseract OCR installed
"""


import fitz
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
import sys
import os
# Import robust PO extraction logic
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from extract_po_details import extract_quantity_and_dock_date, extract_buyer_name

# Configure Tesseract path (update if needed)
# For Linux container, use default system path
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:  # Linux/Unix
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

def preprocess_image(img):
    """
    Apply advanced image preprocessing for better OCR accuracy
    
    Args:
        img: PIL Image object
        
    Returns:
        PIL Image object with preprocessing applied
    """
    img_array = np.array(img)
    
    # Reduce noise with Gaussian blur
    img_array = cv2.GaussianBlur(img_array, (1, 1), 0)
    
    # Sharpen image
    sharpen_kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
    img_array = cv2.filter2D(img_array, -1, sharpen_kernel)
    
    # Enhance contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_array = clahe.apply(img_array)
    
    # Clean up with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
    
    return Image.fromarray(img_array)

def detect_and_correct_rotation(img):
    """
    Detect page orientation and rotate image for optimal OCR
    
    Args:
        img: PIL Image object
        
    Returns:
        tuple: (corrected_image, rotation_angle)
    """
    try:
        osd = pytesseract.image_to_osd(img)
        angle = int([line for line in osd.split('\n') if 'Rotate:' in line][0].split(':')[1].strip())
        
        if angle != 0:
            print(f"Detected rotation: {angle} degrees")
            img = img.rotate(-angle, expand=True)
        
        return img, angle
    except:
        return img, 0

def pdf_to_searchable(input_pdf, output_pdf):
    """
    Convert a PDF to a searchable PDF by adding invisible OCR text overlay
    
    Args:
        input_pdf (str): Path to input PDF file
        output_pdf (str): Path to output searchable PDF file
    """
    pdf_document = fitz.open(input_pdf)
    
    # Check if PDF has any pages
    if len(pdf_document) == 0:
        # Get file info for better diagnostics
        file_size = os.path.getsize(input_pdf)
        metadata = pdf_document.metadata if pdf_document.metadata else {}
        creator = metadata.get('creator', 'Unknown')
        
        pdf_document.close()
        
        # Provide detailed error message based on file characteristics
        if file_size > 5000000:  # > 5MB but 0 pages - likely interrupted multi-page scan
            raise ValueError(f"PDF file '{input_pdf}' contains no pages despite being {file_size:,} bytes. "
                           f"Scanner: {creator}. This indicates an interrupted multi-page scan - the pipeline "
                           f"processed the file before scanning was complete. Solution: Wait longer between "
                           f"pages or scan single pages separately.")
        elif file_size > 1000000:  # 1-5MB but 0 pages
            raise ValueError(f"PDF file '{input_pdf}' contains no pages despite being {file_size:,} bytes. "
                           f"Scanner: {creator}. This indicates a scanner hardware issue - the PDF structure is "
                           f"malformed. Try: 1) Power cycle scanner, 2) Check scanner settings, 3) Test with simple document.")
        else:
            raise ValueError(f"PDF file '{input_pdf}' contains no pages. This usually indicates a corrupted "
                           f"or malformed PDF file. Please re-scan the document.")
    

    output_pdf_doc = fitz.open()

    # Switch: use new full-text extraction and cleaning
    USE_FULL_TEXT_OCR = os.environ.get('USE_FULL_TEXT_OCR', '0') == '1'

    for page_num in range(len(pdf_document)):
        print(f"Processing page {page_num + 1}...")
        page = pdf_document[page_num]
        ocr_matrix = fitz.Matrix(4, 4)
        pix = page.get_pixmap(matrix=ocr_matrix, alpha=False)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data)).convert('L')
        corrected_img, rotation_angle = detect_and_correct_rotation(img)
        processed_img = preprocess_image(corrected_img)



        if USE_FULL_TEXT_OCR:
            # New method: extract and clean full text
            raw_text = pytesseract.image_to_string(processed_img, config='--oem 3 --psm 4')
            cleaned_text = clean_ocr_text(raw_text)
            # Extract quantity, dock date, and buyer name using robust logic
            quantity, dock_date = extract_quantity_and_dock_date(cleaned_text)
            buyer_name = extract_buyer_name(cleaned_text)
            print(f"[EXTRACTED] Quantity: {quantity}, Dock Date: {dock_date}, Buyer: {buyer_name}")
            # Save cleaned text for review (optional)
            with open(f"page_{page_num+1}_cleaned.txt", "w") as f:
                f.write(cleaned_text)
            # Add original page (no overlay)
            new_page = output_pdf_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.show_pdf_page(page.rect, pdf_document, page_num)
            print(f"Full-text OCR (cleaned) saved for page {page_num + 1}")
            continue

        # Original method: word-level overlay
        all_words = {}
        ocr_configs = [
            r'--oem 3 --psm 3',
            r'--oem 3 --psm 6',
            r'--oem 3 --psm 11',
            r'--oem 3 --psm 8',
        ]
        for config in ocr_configs:
            try:
                ocr_result = pytesseract.image_to_data(
                    processed_img,
                    output_type=pytesseract.Output.DICT,
                    config=config
                )
                for i, word in enumerate(ocr_result['text']):
                    if word.strip() and len(ocr_result['conf']) > i:
                        conf = int(ocr_result['conf'][i]) if ocr_result['conf'][i] != '-1' else 0
                        if conf > 5 and ocr_result['level'][i] == 5:
                            x, y = ocr_result['left'][i], ocr_result['top'][i]
                            key = f"{x}_{y}_{word}"
                            if key not in all_words or conf > all_words[key]['conf']:
                                all_words[key] = {
                                    'word': word, 'x': x, 'y': y,
                                    'width': ocr_result['width'][i],
                                    'height': ocr_result['height'][i],
                                    'conf': conf
                                }
            except:
                continue
        if not all_words:
            print(f"OCR failed for page {page_num + 1}, adding original page without text layer")
            new_page = output_pdf_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.show_pdf_page(page.rect, pdf_document, page_num)
            continue
        if rotation_angle in [90, 270]:
            new_page = output_pdf_doc.new_page(width=page.rect.height, height=page.rect.width)
            page_rect = fitz.Rect(0, 0, page.rect.height, page.rect.width)
        else:
            new_page = output_pdf_doc.new_page(width=page.rect.width, height=page.rect.height)
            page_rect = page.rect
        if rotation_angle != 0:
            rotation_matrices = {
                90:  fitz.Matrix(0, 1, -1, 0, page.rect.width, 0),
                180: fitz.Matrix(-1, 0, 0, -1, page.rect.width, page.rect.height),
                270: fitz.Matrix(0, -1, 1, 0, 0, page.rect.height)
            }
            matrix = rotation_matrices[rotation_angle]
            rotated_pix = page.get_pixmap(matrix=matrix, alpha=False)
            new_page.insert_image(page_rect, pixmap=rotated_pix)
        else:
            new_page.show_pdf_page(page_rect, pdf_document, page_num)
        scale_x = page_rect.width / corrected_img.width
        scale_y = page_rect.height / corrected_img.height
        words_added = 0
        for word_data in all_words.values():
            word = word_data['word']
            x, y = word_data['x'], word_data['y']
            width, height = word_data['width'], word_data['height']
            if height < 3 or height > 200 or width < 1:
                continue
            pdf_x, pdf_y = x * scale_x, y * scale_y
            pdf_width, pdf_height = width * scale_x, height * scale_y
            width_scale, height_scale = 1.4, 1.3
            corrected_width = pdf_width * width_scale
            corrected_height = pdf_height * height_scale
            shift_x = -1.5 * scale_x
            shift_y = corrected_height * 0.1
            corrected_x = pdf_x + shift_x
            corrected_y = pdf_y + shift_y
            font_size = max(corrected_height * 0.8, 4)
            baseline_y = corrected_y + corrected_height * 0.8
            try:
                new_page.insert_text(
                    (corrected_x, baseline_y),
                    word,
                    fontsize=font_size,
                    color=(0, 0, 0),
                    render_mode=3
                )
                words_added += 1
            except:
                continue
        print(f"Added {words_added} words to page {page_num + 1}")
    output_pdf_doc.save(output_pdf)
    output_pdf_doc.close()
    pdf_document.close()
    print(f"Searchable PDF saved as {output_pdf}")
def clean_ocr_text(text):
    """
    Clean OCR text by merging lines, removing excessive breaks, and normalizing spaces.
    """
    import re
    # Remove excessive line breaks (keep paragraph breaks)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  # Replace single line breaks with space
    text = re.sub(r'\n{2,}', '\n', text)  # Reduce multiple breaks to one
    # Remove extra spaces
    text = re.sub(r' +', ' ', text)
    # Optionally, fix common OCR errors (e.g., split numbers/words)
    # text = re.sub(r'(\d) (\d)', r'\1\2', text)  # Merge split numbers
    return text

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 3:
        print("Usage: python ocr_pdf_searchable.py input.pdf output.pdf")
        print("\nThis script converts a PDF to a searchable PDF by adding an invisible")
        print("OCR text layer. The output PDF will look identical to the original")
        print("but will be fully searchable and selectable.")
        print("\nRequirements:")
        print("- Tesseract OCR must be installed")
        print("- Required Python packages: PyMuPDF, pytesseract, opencv-python, pillow")
        sys.exit(1)
    
    input_pdf, output_pdf = sys.argv[1], sys.argv[2]
    
    try:
        pdf_to_searchable(input_pdf, output_pdf)
        print(f"\nSuccessfully created searchable PDF: {output_pdf}")
    except FileNotFoundError:
        print(f"Error: Input file '{input_pdf}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

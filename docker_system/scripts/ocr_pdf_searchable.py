"""
PDF OCR Script - Convert PDFs to searchable PDFs with invisible text overlay

This script uses Tesseract OCR to extract text from PDF pages and creates
a searchable PDF by overlaying invisible text at the correct positions.
"""

import io
import os
import sys

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
import cv2


def detect_and_correct_orientation(img: Image.Image):
    """
    Detect page orientation and rotate image for optimal OCR

    Args:
        img: PIL Image object

    Returns:
        tuple: (corrected_image, rotation_angle)
    """
    try:
        osd = pytesseract.image_to_osd(img)
        print(f"OSD output: {osd}")
        angle = int([line for line in osd.split("\n") if "Rotate:" in line][0].split(":")[1].strip())
        print(f"Detected rotation angle: {angle}°")
        if angle != 0:  # Fixed logic: angle 0 is falsy but still valid
            img = img.rotate(angle, expand=True)
            print(f"Applied {angle}° rotation to image")
        else:
            print("No rotation needed - page is correctly oriented")
        return img, angle
    except Exception as e:
        print(f"Orientation detection failed: {e}")
        return img, 0


def preprocess_image(img: Image.Image) -> Image.Image:
    """Light denoise + threshold to improve OCR."""
    arr = np.array(img)
    if len(arr.shape) == 3:
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    else:
        gray = arr
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thr = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(thr)


def pdf_to_searchable(input_pdf: str, output_pdf: str, save_corrected_orientation: bool = False):
    """
    Convert a PDF to a searchable PDF by adding invisible OCR text overlay
    
    Args:
        input_pdf: Path to input PDF file
        output_pdf: Path to output searchable PDF file  
        save_corrected_orientation: If True, saves pages in corrected orientation for better readability
                                   If False, preserves original page orientation (default behavior)
    """
    if not os.path.exists(input_pdf):
        raise FileNotFoundError(input_pdf)

    pdf_document = fitz.open(input_pdf)
    if len(pdf_document) == 0:
        pdf_document.close()
        raise ValueError("Input PDF has no pages")

    output_pdf_doc = fitz.open()

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

        corrected_img, rotation_angle = detect_and_correct_orientation(img)
        processed_img = preprocess_image(corrected_img)

        # OCR word-level data
        ocr = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT, config="--oem 3 --psm 6")

        # Determine page dimensions and rendering approach
        if save_corrected_orientation and rotation_angle != 0:
            # Save with corrected orientation for better readability
            if rotation_angle in [90, 270]:
                new_page = output_pdf_doc.new_page(width=page.rect.height, height=page.rect.width)
                target_rect = fitz.Rect(0, 0, page.rect.height, page.rect.width)
            else:
                new_page = output_pdf_doc.new_page(width=page.rect.width, height=page.rect.height) 
                target_rect = page.rect
            
            # Create a rotated version of the original page for the corrected orientation
            # This requires creating a transformation matrix for the rotation
            if rotation_angle == 90:
                mat = fitz.Matrix(0, 1, -1, 0, page.rect.width, 0)
                render_rect = fitz.Rect(0, 0, page.rect.height, page.rect.width)
            elif rotation_angle == 180:
                mat = fitz.Matrix(-1, 0, 0, -1, page.rect.width, page.rect.height)
                render_rect = page.rect
            elif rotation_angle == 270:
                mat = fitz.Matrix(0, -1, 1, 0, 0, page.rect.height)
                render_rect = fitz.Rect(0, 0, page.rect.height, page.rect.width)
            else:
                mat = fitz.Matrix(1, 0, 0, 1, 0, 0)  # No rotation
                render_rect = page.rect
                
            # Render the page with rotation applied
            temp_pix = page.get_pixmap(matrix=mat * fitz.Matrix(3, 3), alpha=False)
            temp_img = Image.open(io.BytesIO(temp_pix.tobytes("png")))
            
            # Insert the rotated image into the new page
            temp_img_bytes = io.BytesIO()
            temp_img.save(temp_img_bytes, format='PNG')
            temp_img_bytes.seek(0)
            
            new_page.insert_image(target_rect, stream=temp_img_bytes.getvalue())
            
            print(f"Page {page_num + 1}: Corrected orientation by {rotation_angle}° for better readability")
        else:
            # Original behavior: preserve original page orientation
            if rotation_angle in [90, 270]:
                new_page = output_pdf_doc.new_page(width=page.rect.height, height=page.rect.width)
                target_rect = fitz.Rect(0, 0, page.rect.height, page.rect.width)
            else:
                new_page = output_pdf_doc.new_page(width=page.rect.width, height=page.rect.height)
                target_rect = page.rect

            # Always render original page as background (maintains original orientation)
            new_page.show_pdf_page(target_rect, pdf_document, page_num)

        # Map OCR coords to PDF coords
        scale_x = target_rect.width / processed_img.width
        scale_y = target_rect.height / processed_img.height

        words_added = 0
        n = len(ocr["text"]) if "text" in ocr else 0
        for i in range(n):
            txt = (ocr["text"][i] or "").strip()
            if not txt:
                continue
            conf_raw = ocr.get("conf", ["-1"]) [i]
            try:
                conf = int(conf_raw) if conf_raw != "-1" else 0
            except Exception:
                conf = 0
            if conf < 5:
                continue

            x = ocr["left"][i]
            y = ocr["top"][i]
            w = ocr["width"][i]
            h = ocr["height"][i]
            if h <= 1 or w <= 1:
                continue

            pdf_x = x * scale_x
            pdf_y = y * scale_y
            pdf_h = h * scale_y

            # Invisible text (render_mode=3)
            try:
                new_page.insert_text(
                    (pdf_x, pdf_y + pdf_h * 0.85),
                    txt,
                    fontsize=max(pdf_h * 0.9, 4),
                    color=(0, 0, 0),
                    render_mode=3,
                )
                words_added += 1
            except Exception:
                continue

        print(f"Page {page_num + 1}: added {words_added} words")

    output_pdf_doc.save(output_pdf)
    output_pdf_doc.close()
    pdf_document.close()
    print(f"Searchable PDF saved as {output_pdf}")


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python ocr_pdf_searchable.py input.pdf output.pdf [--correct-orientation]")
        print("  --correct-orientation: Save pages in corrected orientation for better readability")
        sys.exit(1)

    input_pdf, output_pdf = sys.argv[1], sys.argv[2]
    save_corrected_orientation = len(sys.argv) == 4 and sys.argv[3] == "--correct-orientation"
    
    try:
        pdf_to_searchable(input_pdf, output_pdf, save_corrected_orientation)
        if save_corrected_orientation:
            print(f"Successfully created searchable PDF with corrected orientation: {output_pdf}")
        else:
            print(f"Successfully created searchable PDF: {output_pdf}")
    except Exception as e:
        # Bubble up errors so caller can log details
        print(f"Error processing PDF: {e}")
        raise


if __name__ == "__main__":
    main()

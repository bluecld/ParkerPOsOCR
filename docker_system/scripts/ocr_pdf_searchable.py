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
        angle = int([line for line in osd.split("\n") if "Rotate:" in line][0].split(":")[1].strip())
        if angle and angle % 360 != 0:
            img = img.rotate(angle, expand=True)
        return img, angle
    except Exception:
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


def pdf_to_searchable(input_pdf: str, output_pdf: str):
    """
    Convert a PDF to a searchable PDF by adding invisible OCR text overlay
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

        # Create output page (respect rotation if changed)
        if rotation_angle in [90, 270]:
            new_page = output_pdf_doc.new_page(width=page.rect.height, height=page.rect.width)
            target_rect = fitz.Rect(0, 0, page.rect.height, page.rect.width)
        else:
            new_page = output_pdf_doc.new_page(width=page.rect.width, height=page.rect.height)
            target_rect = page.rect

        # Always render original page as background
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
    if len(sys.argv) != 3:
        print("Usage: python ocr_pdf_searchable.py input.pdf output.pdf")
        sys.exit(1)

    input_pdf, output_pdf = sys.argv[1], sys.argv[2]
    try:
        pdf_to_searchable(input_pdf, output_pdf)
        print(f"Successfully created searchable PDF: {output_pdf}")
    except Exception as e:
        # Bubble up errors so caller can log details
        print(f"Error processing PDF: {e}")
        raise


if __name__ == "__main__":
    main()

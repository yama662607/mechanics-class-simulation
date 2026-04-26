import os
import sys

import fitz


def extract_pdf_text(pdf_path, start_page=None, end_page=None, quiet=False):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    Returns a list of strings, where each string is the text of one page.
    """
    results = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        start_idx = 0
        if start_page:
            start_idx = max(0, start_page - 1)

        end_idx = total_pages
        if end_page:
            end_idx = min(total_pages, end_page)

        if start_idx >= total_pages:
            if not quiet:
                print(f"Error: Start page {start_page} is out of range", file=sys.stderr)
            return []

        for i in range(start_idx, end_idx):
            page = doc.load_page(i)
            text = page.get_text()
            results.append(text)
            if not quiet:
                print(f"--- Page {i + 1} ---")
                print(text)
                print("\n")

        doc.close()
        return results

    except Exception as e:
        if not quiet:
            print(f"An error occurred during text extraction: {e}", file=sys.stderr)
        return []


def extract_pdf_images(pdf_path, start_page, end_page, out_dir="/tmp", dpi=300):
    """
    Extracts pages as images from a PDF file.
    """
    saved_paths = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page)

        for i in range(start_idx, end_idx):
            page_num = i + 1
            out_path = os.path.join(out_dir, f"page_{page_num}.png")
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)
            pix.save(out_path)
            saved_paths.append(out_path)

        doc.close()
        return saved_paths
    except Exception as e:
        print(f"Error extracting images: {e}", file=sys.stderr)
        return []

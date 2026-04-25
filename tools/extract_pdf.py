"""Extract text and page images from PDF files.

Usage:
    uv run python tools/extract_pdf.py <pdf_path> [--dpi 200] [--ocr]

For each PDF, outputs:
    <stem>_text.txt   – extracted text (if any text layer exists)
    <stem>_p1.png     – page 1 as image
    <stem>_p2.png     – page 2 as image
    ...

Files are written to the same directory as the input PDF.
"""

import argparse
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF


def has_meaningful_text(page: fitz.Page, threshold: int = 30) -> bool:
    """Return True if the page contains more than *threshold* chars of text."""
    text = page.get_text("text").strip()
    return len(text) > threshold


def extract_text(doc: fitz.Document, *, use_ocr: bool = False) -> str:
    """Extract text from all pages of *doc*.

    When *use_ocr* is True **and** Tesseract is available, OCR is attempted on
    pages that lack an embedded text layer.
    """
    parts: list[str] = []

    for page_num, page in enumerate(doc, 1):
        header = f"--- Page {page_num} ---"

        if has_meaningful_text(page):
            parts.append(header)
            parts.append(page.get_text("text").strip())
            continue

        if not use_ocr:
            parts.append(header)
            parts.append("[No text layer detected]")
            continue

        # Attempt Tesseract OCR via PyMuPDF
        try:
            tp = page.get_textpage_ocr(flags=fitz.TEXT_PRESERVE_WHITESPACE)
            ocr_text = page.get_text("text", textpage=tp).strip()
            if ocr_text:
                parts.append(header)
                parts.append(ocr_text)
            else:
                parts.append(header)
                parts.append("[OCR returned no text]")
        except RuntimeError:
            parts.append(header)
            parts.append("[OCR failed – is Tesseract installed?]")

    return "\n\n".join(parts)


def render_pages(doc: fitz.Document, out_dir: Path, stem: str, dpi: int) -> list[Path]:
    """Render each page of *doc* to a PNG file.  Returns list of created paths."""
    created: list[Path] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for page_num, page in enumerate(doc, 1):
        pix = page.get_pixmap(matrix=matrix)
        out_path = out_dir / f"{stem}_p{page_num}.png"
        pix.save(str(out_path))
        created.append(out_path)

    return created


def process_pdf(pdf_path: Path, *, dpi: int = 200, use_ocr: bool = False) -> None:
    """Process a single PDF: extract text and render pages as images."""
    if not pdf_path.is_file():
        print(f"Error: {pdf_path} not found.", file=sys.stderr)
        sys.exit(1)

    out_dir = pdf_path.parent
    stem = pdf_path.stem

    doc = fitz.open(str(pdf_path))
    page_count = len(doc)
    print(f"Processing: {pdf_path.name} ({page_count} pages)")

    # --- Text extraction ---
    text = extract_text(doc, use_ocr=use_ocr)
    text_path = out_dir / f"{stem}_text.txt"
    text_path.write_text(text, encoding="utf-8")
    print(f"  Text → {os.path.relpath(text_path)}")

    # --- Page image rendering ---
    images = render_pages(doc, out_dir, stem, dpi)
    for img in images:
        print(f"  Image → {os.path.relpath(img)}")

    doc.close()
    print(f"Done. {len(images)} images + 1 text file created.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text and page images from a PDF file."
    )
    parser.add_argument("pdf", type=Path, help="Path to the PDF file.")
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Resolution for page images (default: 200).",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Attempt Tesseract OCR on pages without a text layer.",
    )
    args = parser.parse_args()
    process_pdf(args.pdf, dpi=args.dpi, use_ocr=args.ocr)


if __name__ == "__main__":
    main()

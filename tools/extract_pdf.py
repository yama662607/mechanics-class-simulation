"""Unified PDF text / formula extractor.

Modes:
  auto      : per page, simple if text layer exists else OCR, AND latex via
              pix2text on the matching pre-rendered PNG. Requires --image-dir.
              Default.
  simple    : pymupdf only — fastest, requires PDF with embedded text.
  ocr       : easyocr — for scanned / image-only PDFs.  `uv sync --extra ocr`.
  latex     : pix2text only — extract LaTeX math from page images.
              Requires --image-dir.  `uv sync --extra math`.

The two-file split (render_pdf.py + extract_pdf.py) is intentional: it forces
agents to render and visually review page images before writing qmd. Earlier
versions bundled rendering inside extraction and agents repeatedly wrote qmd
from text/latex alone, missing figures, equation numbers, and OCR errors that
only the image makes obvious. Do not bypass --image-dir.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "utils"))

import fitz  # noqa: E402  (pymupdf — required for every mode except `latex`)

# ---------------------------------------------------------------------------
# Diagnose
# ---------------------------------------------------------------------------


def diagnose(pdf_path: str) -> int:
    """Print structure summary so the caller can pick the right --mode."""
    if not os.path.exists(pdf_path):
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        return 1

    with fitz.open(pdf_path) as doc:
        total = len(doc)
        print(f"=== {pdf_path} ===")
        print(f"Pages: {total}")
        md = doc.metadata or {}
        for key in ("title", "author", "producer", "creator"):
            if md.get(key):
                print(f"  {key}: {md[key]}")

        sample_indices = sorted({0, total // 4, total // 2, (3 * total) // 4, total - 1} - {-1})
        text_pages = 0
        for idx in sample_indices:
            if idx < 0 or idx >= total:
                continue
            page = doc.load_page(idx)
            text = (page.get_text() or "").strip()
            n_images = len(page.get_images(full=True))
            has_text = len(text) > 30
            text_pages += int(has_text)
            preview = text[:80].replace("\n", " ")
            flag = "TEXT" if has_text else "no-text"
            print(
                f"  p.{idx + 1:>4}: {flag:<7} chars={len(text):>5}  images={n_images}  '{preview}'"
            )

    if text_pages >= len(sample_indices) // 2:
        print("\nRecommendation: --mode simple (text layer present)")
    else:
        print("\nRecommendation: --mode ocr (text layer missing — install `--extra ocr`)")
    return 0


# ---------------------------------------------------------------------------
# Page iteration helpers
# ---------------------------------------------------------------------------


def _page_range(doc: fitz.Document, start: int | None, end: int | None) -> range:
    total = len(doc)
    if start is not None and start < 1:
        raise ValueError(f"--start must be >= 1 (got {start})")
    if end is not None and end < 1:
        raise ValueError(f"--end must be >= 1 (got {end})")
    if start is not None and end is not None and start > end:
        raise ValueError(f"--start ({start}) cannot exceed --end ({end})")
    s = max(0, (start or 1) - 1)
    e = min(total, end or total)
    if s >= total:
        raise ValueError(f"start page {start} out of range (total={total})")
    return range(s, e)


def _page_has_text(page: fitz.Page, threshold: int = 30) -> bool:
    return len((page.get_text() or "").strip()) > threshold


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def mode_simple(pdf_path: str, start: int | None, end: int | None) -> int:
    with fitz.open(pdf_path) as doc:
        for i in _page_range(doc, start, end):
            page = doc.load_page(i)
            text = page.get_text() or ""
            print(f"--- Page {i + 1} ---")
            print(text or "[No text layer — try --mode ocr]")
            print()
    return 0


def _ocr_reader(langs: list[str]):
    try:
        import easyocr  # type: ignore
    except ImportError:
        print("easyocr is not installed. Run: uv sync --extra ocr", file=sys.stderr)
        sys.exit(2)
    return easyocr.Reader(langs, gpu=False)


def _ocr_page(reader, page: fitz.Page, dpi: int = 200) -> str:
    pix = page.get_pixmap(dpi=dpi)
    img_bytes = pix.tobytes("png")
    lines = reader.readtext(img_bytes, detail=0, paragraph=True)
    return "\n".join(lines)


def mode_ocr(pdf_path: str, start: int | None, end: int | None, langs: list[str]) -> int:
    reader = _ocr_reader(langs)
    with fitz.open(pdf_path) as doc:
        for i in _page_range(doc, start, end):
            page = doc.load_page(i)
            text = _ocr_page(reader, page)
            print(f"--- Page {i + 1} (OCR) ---")
            print(text)
            print()
    return 0


def _try_pix2text():
    """Return a Pix2Text instance, or None if pix2text is not installed.

    LaTeX extraction is best-effort in auto mode: missing extra → skip + warn,
    rather than fail the whole extraction.
    """
    try:
        from pix2text import Pix2Text  # type: ignore
    except ImportError:
        print(
            "note: pix2text not installed — skipping LaTeX extraction.\n"
            "      install with: uv sync --extra math",
            file=sys.stderr,
        )
        return None
    return Pix2Text(device="cpu")


def _pix2text_one(p2t, image_path: Path) -> str:
    if not image_path.exists():
        return f"[image missing: {image_path}]"
    res = p2t.recognize(str(image_path))
    if isinstance(res, str):
        return res
    return "\n".join(item.get("text", "") for item in res)


def mode_auto(
    pdf_path: str,
    start: int | None,
    end: int | None,
    langs: list[str],
    image_dir: str | None,
) -> int:
    """Per-page: simple-or-OCR for text + pix2text for LaTeX (default-on)."""
    if image_dir is None:
        print(
            "Error: --image-dir is required for auto mode.\n"
            "  1. Render images:  just render-pdf <pdf> <start> <end>\n"
            "  2. Then extract:   just extract-pdf <pdf> <start> <end>\n"
            "  (`just extract-pdf` runs render-pdf first and passes --image-dir.)\n"
            "\n"
            "  This 2-step is intentional. AI agents MUST visually review the\n"
            "  rendered PNGs before writing qmd — text + LaTeX alone miss figure\n"
            "  layouts, equation numbers, and OCR errors. Do not bypass.\n"
            "\n"
            "  If you genuinely only need text (no images, no LaTeX), use\n"
            "  --mode simple or --mode ocr.",
            file=sys.stderr,
        )
        return 2

    image_root = Path(image_dir)
    p2t = _try_pix2text()

    with fitz.open(pdf_path) as doc:
        pages = list(_page_range(doc, start, end))
        needs_ocr = [i for i in pages if not _page_has_text(doc.load_page(i))]
        reader = _ocr_reader(langs) if needs_ocr else None

        for i in pages:
            page = doc.load_page(i)
            png_path = image_root / f"page_{i + 1}.png"

            if _page_has_text(page):
                source = "text"
                body = page.get_text() or ""
            else:
                source = "OCR"
                body = _ocr_page(reader, page)  # type: ignore[arg-type]

            if p2t is not None:
                latex = _pix2text_one(p2t, png_path)
                print(f"--- Page {i + 1} ({source} + LaTeX) ---")
                print(body.rstrip())
                print(f"\n[LaTeX from {png_path.name}]")
                print(latex.rstrip())
            else:
                print(f"--- Page {i + 1} ({source}) ---")
                print(body.rstrip())
            print()
    return 0


_REVIEW_BANNER = """\
================================================================================
  REMINDER — text + LaTeX is INCOMPLETE without visually reviewing the PNGs.
  Open every page image in {image_dir} (Read tool / file viewer) before
  writing qmd. Figure layouts, equation numbers, and silent OCR errors are
  only catchable in the rendered image. AGENTS.md treats this as mandatory.
================================================================================
"""


def mode_latex(pdf_path: str, start: int | None, end: int | None, image_dir: str | None) -> int:
    if not image_dir:
        print(
            "Error: --image-dir is required for --mode latex.\n"
            "Run `just render-pdf <pdf> <start> <end>` first.",
            file=sys.stderr,
        )
        return 2

    from latex_extraction import extract_latex_from_images  # noqa: E402

    image_paths = []
    with fitz.open(pdf_path) as doc:
        for i in _page_range(doc, start, end):
            candidate = Path(image_dir) / f"page_{i + 1}.png"
            if candidate.exists():
                image_paths.append(str(candidate))
            else:
                print(
                    f"Warning: missing {candidate} (run render-pdf first)",
                    file=sys.stderr,
                )

    results = extract_latex_from_images(image_paths, quiet=False)
    return 0 if results else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _ensure_utf8_stdout() -> None:
    """Avoid UnicodeEncodeError on Windows (default cp932) when printing
    extracted text containing Japanese / math symbols / non-ASCII glyphs."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, AttributeError):
                pass


def main() -> int:
    _ensure_utf8_stdout()
    p = argparse.ArgumentParser(
        description="Extract text / OCR / LaTeX from a PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Modes:", 1)[-1] if __doc__ else "",
    )
    p.add_argument("pdf_path", help="Path to PDF")
    p.add_argument("--start", type=int, default=None, help="Start page (1-indexed)")
    p.add_argument("--end", type=int, default=None, help="End page (inclusive)")
    p.add_argument(
        "--mode",
        choices=["auto", "simple", "ocr", "latex"],
        default="auto",
        help="Extraction backend (default: auto)",
    )
    p.add_argument(
        "--diagnose",
        action="store_true",
        help="Print PDF structure summary and exit (no extraction).",
    )
    p.add_argument(
        "--image-dir",
        default=None,
        help="Directory of pre-rendered PNGs (required for --mode latex).",
    )
    p.add_argument(
        "--lang",
        nargs="+",
        default=["en"],
        help="OCR languages (e.g. --lang en ja). Used by ocr/auto modes.",
    )
    args = p.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF not found: {args.pdf_path}", file=sys.stderr)
        return 1

    if args.diagnose:
        return diagnose(args.pdf_path)

    if args.mode in ("auto", "latex") and args.image_dir:
        print(_REVIEW_BANNER.format(image_dir=args.image_dir))

    try:
        if args.mode == "simple":
            return mode_simple(args.pdf_path, args.start, args.end)
        if args.mode == "ocr":
            return mode_ocr(args.pdf_path, args.start, args.end, args.lang)
        if args.mode == "latex":
            return mode_latex(args.pdf_path, args.start, args.end, args.image_dir)
        return mode_auto(args.pdf_path, args.start, args.end, args.lang, args.image_dir)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

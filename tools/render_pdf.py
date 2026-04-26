"""Render PDF pages to PNG images for visual review.

Pair with `tools/extract_pdf.py` so you have BOTH visual and textual
representations before writing qmd (see AGENTS.md).
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

# Add tools/utils to path so the helper module imports work whether the
# script is invoked from the project root or anywhere else.
sys.path.append(str(Path(__file__).resolve().parent / "utils"))

try:
    from pdf_processing import extract_pdf_images  # noqa: E402
except ImportError as exc:
    print(f"Error: could not import pdf_processing from utils: {exc}", file=sys.stderr)
    sys.exit(1)


def _ensure_utf8_stdout() -> None:
    """Avoid UnicodeEncodeError on Windows (default cp932)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, AttributeError):
                pass


def main() -> int:
    _ensure_utf8_stdout()

    parser = argparse.ArgumentParser(description="Render PDF pages as PNG images.")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--start", type=int, default=1, help="Start page (1-based)")
    parser.add_argument("--end", type=int, default=1, help="End page (1-based)")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for images")
    parser.add_argument(
        "--out-dir",
        "--out_dir",  # back-compat with the old underscore form
        default=tempfile.gettempdir(),
        help="Output directory for images (default: system temp dir)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: file not found: {args.pdf_path}", file=sys.stderr)
        return 1
    if args.start < 1:
        print(f"Error: --start must be >= 1 (got {args.start})", file=sys.stderr)
        return 2
    if args.end < args.start:
        print(
            f"Error: --end ({args.end}) must be >= --start ({args.start})",
            file=sys.stderr,
        )
        return 2

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    print(f"Rendering PDF pages {args.start}-{args.end} to {args.out_dir}...")
    image_paths = extract_pdf_images(
        args.pdf_path, args.start, args.end, out_dir=args.out_dir, dpi=args.dpi
    )

    if not image_paths:
        print("Failed to render images.", file=sys.stderr)
        return 1

    print("\nRendering complete. Saved images:")
    for path in image_paths:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

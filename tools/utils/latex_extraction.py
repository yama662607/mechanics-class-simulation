import argparse
import os
import sys


def extract_latex_from_images(image_paths, quiet=False):
    """Extract LaTeX from a list of image paths using Pix2Text.

    Returns a list of strings (one per image). On unrecoverable errors
    (model load failure etc.) the exception is re-raised so callers can
    distinguish "no input" from "extractor crashed".
    """
    try:
        from pix2text import Pix2Text
    except ImportError:
        print(
            "pix2text is not installed. Run: uv sync --extra math",
            file=sys.stderr,
        )
        return []

    p2t = Pix2Text(device="cpu")
    results = []
    for img_path in image_paths:
        if not os.path.exists(img_path):
            if not quiet:
                print(f"Warning: image not found at {img_path}", file=sys.stderr)
            results.append("")
            continue

        res = p2t.recognize(img_path)
        if isinstance(res, str):
            text = res
        else:
            text = "\n".join(item.get("text", "") for item in res)
        results.append(text)

        if not quiet:
            print(f"--- Extracted LaTeX from {os.path.basename(img_path)} ---")
            print(text)
            print()
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract LaTeX from images using Pix2Text.")
    parser.add_argument("image_paths", nargs="+", help="Paths to images")

    args = parser.parse_args()
    extract_latex_from_images(args.image_paths)

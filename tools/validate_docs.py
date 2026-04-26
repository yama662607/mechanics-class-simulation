import argparse
import concurrent.futures
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypedDict

from utils.find_quarto import find_quarto

# --- Configuration ---
NODE_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "utils", "mermaid_parser.js")
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".validation_cache.json")
DOCS_DIR = "quarto"
VALIDATOR_VERSION = "2"
MERMAID_PATTERN = re.compile(r"```\{mermaid\}(.*?)```", re.DOTALL | re.IGNORECASE)
LATEX_INLINE_PATTERN = re.compile(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$", re.DOTALL)  # $...$
LATEX_BLOCK_PATTERN = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)  # $$...$$
FENCED_CODE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")

# Try importing pylatexenc
try:
    from pylatexenc.latexwalker import LatexWalker, LatexWalkerError

    HAS_PYLATEXENC = True
except ImportError:
    HAS_PYLATEXENC = False


class ValidationResult(TypedDict):
    file: str
    errors: list[str]
    mermaid_blocks: list[dict[str, Any]]
    hash: str | None
    fixed: bool


# --- Caching Logic ---


def get_file_hash(filepath: str) -> str:
    """Calculates SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_validator_hash() -> str:
    """Calculates a hash for the validator implementation itself."""
    hasher = hashlib.sha256()
    hasher.update(VALIDATOR_VERSION.encode())

    for path in [__file__, NODE_SCRIPT_PATH]:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

    return hasher.hexdigest()


def load_cache() -> dict[str, Any]:
    """Loads validation cache from JSON file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: dict[str, Any]) -> None:
    """Saves validation cache to JSON file."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  Could not save cache: {e}")


# --- Validation Logic ---


def check_quarto_structure(filepath: str) -> list[str]:
    """Checks general Quarto structure using Pandoc AST dry-run."""
    errors = []
    quarto_bin = find_quarto()
    if quarto_bin is None:
        errors.append("[Structure] Quarto binary not found. Skipping structure check.")
        return errors
    try:
        cmd = [quarto_bin, "pandoc", filepath, "-t", "json"]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        errors.append(f"[Structure] {e.stderr.strip()}")
    return errors


def check_fenced_divs(filepath: str, lines: list[str], do_fix: bool = False) -> dict[str, Any]:
    """Checks for blank lines before fences. Returns results and fixed lines if requested."""
    errors = []
    fixed_lines = list(lines)
    offset = 0
    in_code_block = False
    in_frontmatter = False

    for i, line in enumerate(lines):
        stripped_line = line.strip()

        if i == 0 and stripped_line == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped_line == "---":
                in_frontmatter = False
            continue

        if stripped_line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if stripped_line.startswith(":::"):
            if i > 0:
                prev_line = fixed_lines[i + offset - 1].strip()
                if prev_line and prev_line != "---":
                    # We allow consecutive ::: for nested divs if desired,
                    # but typically Quarto/Pandoc prefer blank lines between them too.
                    if not prev_line.startswith(":::"):
                        errors.append(
                            f"[Style] Line {i + 1}: Fenced div boundary ':::' must be preceded by a blank line."
                        )
                        if do_fix:
                            fixed_lines.insert(i + offset, "")
                            offset += 1
            continue

        # --- New check: lists inside fenced divs ---
        # Detect if we are inside a fenced div block (roughly)
        # We look for a line starting with list markers (1. , - , * )
        # that is immediately preceded by a non-blank line that is not a list item.
        if (
            stripped_line.startswith("1. ")
            or stripped_line.startswith("- ")
            or stripped_line.startswith("* ")
        ):
            if i > 0:
                # Check preceding line in fixed_lines (including potentially inserted lines)
                prev_idx = i + offset - 1
                if prev_idx >= 0:
                    prev_line = fixed_lines[prev_idx].strip()
                    # If the previous line is not blank AND not another list item AND not a fence separator
                    # AND we are likely inside a block (heuristic: recent line was a ::: or a header)
                    is_prev_list = (
                        prev_line.startswith("1. ")
                        or prev_line.startswith("- ")
                        or prev_line.startswith("* ")
                    )
                    is_prev_fence = prev_line.startswith(":::")
                    if prev_line and not is_prev_list and not is_prev_fence:
                        # Specifically check if we are inside a definition/theorem block
                        # by looking back a few lines for the opening ::: {#def or similar
                        is_inside_block = False
                        for j in range(max(0, i - 10), i):
                            if lines[j].strip().startswith("::: {#"):
                                is_inside_block = True
                                break

                        if is_inside_block:
                            errors.append(
                                f"[Style] Line {i + 1}: List item '{stripped_line[:3]}...' inside block should be preceded by a blank line for correct rendering."
                            )
                            if do_fix:
                                fixed_lines.insert(i + offset, "")
                                offset += 1

    return {"errors": errors, "fixed_lines": fixed_lines if do_fix else None}


def strip_markdown_code(content: str) -> str:
    """Removes Markdown code spans/blocks before math regex validation."""
    content = FENCED_CODE_PATTERN.sub(lambda match: "\n" * match.group(0).count("\n"), content)
    return INLINE_CODE_PATTERN.sub("", content)


def check_latex(filepath: str, content: str) -> list[str]:
    """Validates LaTeX math blocks."""
    errors = []
    content = strip_markdown_code(content)

    def validate_math_block(math_code: str, line_no_estimate: int, block_type: str):
        if not math_code.strip():
            return

        open_braces = math_code.count("{")
        close_braces = math_code.count("}")
        if open_braces != close_braces:
            errors.append(
                f"[LaTeX] Approx Line {line_no_estimate}: Unbalanced braces in {block_type} math."
            )

        if HAS_PYLATEXENC:
            try:
                walker = LatexWalker(math_code)
                walker.get_latex_nodes()
            except LatexWalkerError as e:
                errors.append(f"[LaTeX] Approx Line {line_no_estimate}: Parse error: {str(e)}")
            except Exception as e:
                errors.append(f"[LaTeX] Approx Line {line_no_estimate}: Unexpected error: {str(e)}")

    for match in LATEX_BLOCK_PATTERN.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        validate_math_block(match.group(1), line_no, "Display")

    for match in LATEX_INLINE_PATTERN.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        validate_math_block(match.group(1), line_no, "Inline")

    return errors


def collect_mermaid_blocks(filepath: str, content: str) -> list[dict[str, Any]]:
    """Extracts mermaid blocks for batch validation."""
    blocks = []
    for match in MERMAID_PATTERN.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        code = match.group(1)
        blocks.append({"file": filepath, "line": line_no, "code": code})
    return blocks


def validate_file(filepath: str, do_fix: bool = False) -> ValidationResult:
    """Runs Python-side checks and returns mermaid blocks for batching."""
    results: ValidationResult = {
        "file": filepath,
        "errors": [],
        "mermaid_blocks": [],
        "hash": None,
        "fixed": False,
    }

    try:
        results["hash"] = get_file_hash(filepath)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        results["errors"].append(f"[System] Could not read file: {e}")
        return results

    results["errors"].extend(check_quarto_structure(filepath))

    # Fenced div check with optional fix
    div_results = check_fenced_divs(filepath, lines, do_fix=do_fix)
    results["errors"].extend(div_results["errors"])

    if do_fix and div_results["fixed_lines"] is not None and len(div_results["errors"]) > 0:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(div_results["fixed_lines"]) + "\n")
            results["fixed"] = True
            # Re-read content for other checks if needed, but here we just update results
            content = "\n".join(div_results["fixed_lines"])
        except Exception as e:
            results["errors"].append(f"[System] Could not write fix to file: {e}")

    results["errors"].extend(check_latex(filepath, content))
    results["mermaid_blocks"] = collect_mermaid_blocks(filepath, content)

    return results


def run_mermaid_batch_validation(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sends all collected mermaid blocks to Node.js validator."""
    if not blocks:
        return []

    payload = json.dumps({"blocks": blocks})

    try:
        process = subprocess.Popen(
            ["node", NODE_SCRIPT_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=payload)

        if process.returncode != 0:
            print(f" Node.js validator crashed: {stderr}")
            return []

        response = json.loads(stdout)
        return response.get("results", [])

    except FileNotFoundError:
        print(" 'node' command not found or script missing.")
        return []
    except json.JSONDecodeError:
        print(f" Failed to parse Node.js output: {stdout}")
        return []
    except Exception as e:
        print(f" Error running Mermaid validator: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Integrated Document Validator")
    parser.add_argument("target", nargs="?", default=DOCS_DIR, help="Directory or file to validate")
    parser.add_argument("--clear-cache", action="store_true", help="Clear validation cache")
    parser.add_argument("--fix", action="store_true", help="Automatically fix style issues")
    parser.add_argument(
        "--no-cache", action="store_true", help="Ignore validation cache for this run"
    )
    args = parser.parse_args()

    if (args.clear_cache or args.no_cache) and os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print(" Cache cleared.")

    if not HAS_PYLATEXENC:
        print("  'pylatexenc' not found. LaTeX syntax checking will be limited to regex.")

    # Collect files
    files = []
    if os.path.isfile(args.target):
        files.append(args.target)
    else:
        files = glob.glob(os.path.join(args.target, "**/*.qmd"), recursive=True)

    if not files:
        print("No .qmd files found.")
        sys.exit(0)

    # Caching Phase
    validator_hash = get_validator_hash()
    cache = {} if args.no_cache else load_cache()
    files_to_validate = []
    skipped_count = 0

    for f in files:
        abs_path = os.path.abspath(f)
        current_hash = get_file_hash(f)
        cached_info = cache.get(abs_path)

        if (
            cached_info
            and cached_info.get("hash") == current_hash
            and cached_info.get("validator_hash") == validator_hash
            and cached_info.get("passed")
        ):
            skipped_count += 1
        else:
            files_to_validate.append(f)

    if skipped_count > 0:
        print(f"  ⏭  {skipped_count} files skipped (unchanged)")

    if not files_to_validate:
        print("\n All files passed cache check. No new validation needed.")
        sys.exit(0)

    print(f"   Validating {len(files_to_validate)} changed files...\n")

    all_mermaid_blocks = []
    file_results = {}
    file_errors = {}

    # Phase 1: Parallel File Processing (Python checks)
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(validate_file, f, args.fix): f for f in files_to_validate}
        for future in concurrent.futures.as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                res = future.result()
                file_results[filename] = res
                if res["fixed"]:
                    print(f"   Fixed style issues in {filename}")
                if res["errors"]:
                    file_errors[filename] = res["errors"]
                if res["mermaid_blocks"]:
                    all_mermaid_blocks.extend(res["mermaid_blocks"])
            except Exception as e:
                print(f"   Error processing {filename}: {e}")

    # Phase 2: Batch Mermaid Validation
    if all_mermaid_blocks:
        print(f"   Validating {len(all_mermaid_blocks)} Mermaid diagrams...")
        mermaid_results = run_mermaid_batch_validation(all_mermaid_blocks)

        for mermaid_result in mermaid_results:
            if not mermaid_result["valid"]:
                filepath = mermaid_result["file"]
                if filepath not in file_errors:
                    file_errors[filepath] = []
                msg = mermaid_result["message"].split("\n")[0]
                file_errors[filepath].append(f"[Mermaid] Line {mermaid_result['line']}: {msg}")

    # Finalize Cache and Reporting
    for f in files_to_validate:
        abs_path = os.path.abspath(f)
        is_valid = f not in file_errors
        # Calculate hash here or use stored one
        cache[abs_path] = {
            "hash": file_results[f]["hash"],
            "validator_hash": validator_hash,
            "passed": is_valid,
        }

    save_cache(cache)

    if file_errors:
        print("\n" + "!" * 50)
        print(" Validation Issues Found")
        print("!" * 50)
        for f, errors in file_errors.items():
            print(f"\n {f}:")
            for err in errors:
                print(f"    - {err}")
        print("\n" + "!" * 50)
        sys.exit(1)
    else:
        print("\n All checks passed! (Quarto Structure, Style, LaTeX, Mermaid)")
        sys.exit(0)


if __name__ == "__main__":
    main()

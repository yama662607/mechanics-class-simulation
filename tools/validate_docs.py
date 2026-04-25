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
from pathlib import Path
from typing import Any, TypedDict

from utils.find_quarto import find_quarto

NODE_SCRIPT_PATH = Path(__file__).parent / "utils" / "mermaid_parser.js"
CACHE_FILE = Path(__file__).parent / ".validation_cache.json"
DOCS_DIR = "quarto"
VALIDATOR_VERSION = "2"
MERMAID_PATTERN = re.compile(r"```\{mermaid\}(.*?)```", re.DOTALL | re.IGNORECASE)
LATEX_INLINE_PATTERN = re.compile(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$", re.DOTALL)
LATEX_BLOCK_PATTERN = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
FENCED_CODE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]+`")

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


def get_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_validator_hash() -> str:
    hasher = hashlib.sha256()
    hasher.update(VALIDATOR_VERSION.encode())
    for path in [Path(__file__), NODE_SCRIPT_PATH]:
        if not path.exists():
            continue
        with open(path, "rb") as file:
            while chunk := file.read(8192):
                hasher.update(chunk)
    return hasher.hexdigest()


def load_cache() -> dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_cache(cache: dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(cache, file, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"Could not save validation cache: {exc}")


def check_quarto_structure(filepath: str) -> list[str]:
    quarto_bin = find_quarto()
    if quarto_bin is None:
        return ["[Structure] Quarto binary not found. Skipping structure check."]

    try:
        subprocess.run(
            [quarto_bin, "pandoc", filepath, "-t", "json"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return [f"[Structure] {exc.stderr.strip()}"]

    return []


def check_fenced_divs(lines: list[str], do_fix: bool = False) -> dict[str, Any]:
    errors = []
    fixed_lines = list(lines)
    offset = 0
    in_code_block = False
    in_frontmatter = False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if index == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if not stripped.startswith(":::") or index == 0:
            continue

        prev_line = fixed_lines[index + offset - 1].strip()
        if prev_line and prev_line != "---" and not prev_line.startswith(":::"):
            errors.append(
                f"[Style] Line {index + 1}: fenced div boundary must be preceded by a blank line."
            )
            if do_fix:
                fixed_lines.insert(index + offset, "")
                offset += 1

    return {"errors": errors, "fixed_lines": fixed_lines if do_fix else None}


def strip_markdown_code(content: str) -> str:
    content = FENCED_CODE_PATTERN.sub(
        lambda match: "\n" * match.group(0).count("\n"), content
    )
    return INLINE_CODE_PATTERN.sub("", content)


def check_latex(content: str) -> list[str]:
    errors = []
    content = strip_markdown_code(content)

    def validate_math_block(math_code: str, line_no: int, block_type: str) -> None:
        if not math_code.strip():
            return

        if math_code.count("{") != math_code.count("}"):
            errors.append(
                f"[LaTeX] Approx line {line_no}: unbalanced braces in {block_type} math."
            )

        if not HAS_PYLATEXENC:
            return

        try:
            LatexWalker(math_code).get_latex_nodes()
        except LatexWalkerError as exc:
            errors.append(f"[LaTeX] Approx line {line_no}: parse error: {exc}")
        except Exception as exc:
            errors.append(f"[LaTeX] Approx line {line_no}: unexpected error: {exc}")

    for match in LATEX_BLOCK_PATTERN.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        validate_math_block(match.group(1), line_no, "display")

    for match in LATEX_INLINE_PATTERN.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        validate_math_block(match.group(1), line_no, "inline")

    return errors


def collect_mermaid_blocks(filepath: str, content: str) -> list[dict[str, Any]]:
    blocks = []
    for match in MERMAID_PATTERN.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        blocks.append({"file": filepath, "line": line_no, "code": match.group(1)})
    return blocks


def validate_file(filepath: str, do_fix: bool = False) -> ValidationResult:
    results: ValidationResult = {
        "file": filepath,
        "errors": [],
        "mermaid_blocks": [],
        "hash": None,
        "fixed": False,
    }

    try:
        results["hash"] = get_file_hash(filepath)
        with open(filepath, encoding="utf-8") as file:
            content = file.read()
        lines = content.splitlines()
    except Exception as exc:
        results["errors"].append(f"[System] Could not read file: {exc}")
        return results

    results["errors"].extend(check_quarto_structure(filepath))

    div_results = check_fenced_divs(lines, do_fix=do_fix)
    results["errors"].extend(div_results["errors"])
    if do_fix and div_results["fixed_lines"] is not None and div_results["errors"]:
        try:
            content = "\n".join(div_results["fixed_lines"]) + "\n"
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(content)
            results["fixed"] = True
        except Exception as exc:
            results["errors"].append(f"[System] Could not write fix: {exc}")

    results["errors"].extend(check_latex(content))
    results["mermaid_blocks"] = collect_mermaid_blocks(filepath, content)
    return results


def run_mermaid_batch_validation(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not blocks:
        return []

    try:
        process = subprocess.Popen(
            ["node", str(NODE_SCRIPT_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=json.dumps({"blocks": blocks}))
    except FileNotFoundError:
        print("Node command not found. Skipping Mermaid validation.")
        return []

    if process.returncode != 0:
        print(f"Mermaid validator failed: {stderr}")
        return []

    try:
        return json.loads(stdout).get("results", [])
    except json.JSONDecodeError:
        print(f"Could not parse Mermaid validator output: {stdout}")
        return []


def collect_qmd_files(target: str) -> list[str]:
    if os.path.isfile(target):
        return [target]
    return glob.glob(os.path.join(target, "**/*.qmd"), recursive=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Quarto notes.")
    parser.add_argument("target", nargs="?", default=DOCS_DIR)
    parser.add_argument("--clear-cache", action="store_true")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    if (args.clear_cache or args.no_cache) and CACHE_FILE.exists():
        CACHE_FILE.unlink()
        print("Validation cache cleared.")

    if not HAS_PYLATEXENC:
        print("pylatexenc not found. LaTeX checks are limited.")

    files = collect_qmd_files(args.target)
    if not files:
        print("No .qmd files found.")
        return

    validator_hash = get_validator_hash()
    cache = {} if args.no_cache else load_cache()
    files_to_validate = []
    skipped_count = 0
    for file in files:
        abs_path = os.path.abspath(file)
        current_hash = get_file_hash(file)
        cached_info = cache.get(abs_path)
        if (
            cached_info
            and cached_info.get("hash") == current_hash
            and cached_info.get("validator_hash") == validator_hash
            and cached_info.get("passed")
        ):
            skipped_count += 1
        else:
            files_to_validate.append(file)

    if skipped_count:
        print(f"{skipped_count} files skipped by cache.")

    if not files_to_validate:
        print("All files passed cache check.")
        return

    all_mermaid_blocks = []
    file_results = {}
    file_errors = {}

    with ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(validate_file, file, args.fix): file
            for file in files_to_validate
        }
        for future in concurrent.futures.as_completed(future_to_file):
            filename = future_to_file[future]
            result = future.result()
            file_results[filename] = result
            if result["fixed"]:
                print(f"Fixed style issues in {filename}")
            if result["errors"]:
                file_errors[filename] = result["errors"]
            all_mermaid_blocks.extend(result["mermaid_blocks"])

    for mermaid_result in run_mermaid_batch_validation(all_mermaid_blocks):
        if mermaid_result["valid"]:
            continue
        filepath = mermaid_result["file"]
        file_errors.setdefault(filepath, [])
        msg = mermaid_result["message"].split("\n")[0]
        file_errors[filepath].append(f"[Mermaid] Line {mermaid_result['line']}: {msg}")

    for file in files_to_validate:
        abs_path = os.path.abspath(file)
        cache[abs_path] = {
            "hash": file_results[file]["hash"],
            "validator_hash": validator_hash,
            "passed": file not in file_errors,
        }
    save_cache(cache)

    if file_errors:
        print("\nValidation issues found")
        for file, errors in file_errors.items():
            print(f"\n{file}:")
            for error in errors:
                print(f"  - {error}")
        sys.exit(1)

    print("All document checks passed.")


if __name__ == "__main__":
    main()

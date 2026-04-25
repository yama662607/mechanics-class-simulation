import shutil
from pathlib import Path


def clean() -> None:
    project_root = Path(__file__).parent.parent.resolve()
    targets = [
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "quarto/_freeze",
        "quarto/_output",
        "quarto/theory/textbook_files",
    ]

    for target_rel in targets:
        target_path = project_root / target_rel
        if target_path.is_dir():
            shutil.rmtree(target_path)
            print(f"Removed directory: {target_rel}")
        elif target_path.exists():
            target_path.unlink()
            print(f"Removed file: {target_rel}")

    for path in project_root.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)

    for path in project_root.rglob("*.pyc"):
        try:
            path.unlink()
        except OSError:
            pass

    print("Cleanup complete.")


if __name__ == "__main__":
    clean()

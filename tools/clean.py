import shutil
import sys
from pathlib import Path


def clean():
    project_root = Path(__file__).parent.parent.resolve()

    # 削除対象 (固定パス)
    # 注: quarto/_freeze は commit する設計なので削除しない
    fixed_targets = [
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "quarto/_book",
        "quarto/.quarto",
    ]

    # 削除対象 (グロブ)
    glob_targets = [
        "quarto/**/*_files",  # any *_files dir produced by Quarto rendering
        "**/__pycache__",
        "**/*.pyc",
    ]

    print("Cleaning build artifacts...")

    for target_rel in fixed_targets:
        target_path = project_root / target_rel
        if target_path.exists():
            try:
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                print(f"  removed: {target_rel}")
            except Exception as e:
                print(f"  failed to remove {target_rel}: {e}")

    for pattern in glob_targets:
        for p in project_root.glob(pattern):
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
                print(f"  removed: {p.relative_to(project_root)}")
            except OSError as e:
                # Permission denied / file in use — surface but keep going.
                print(f"  skip {p.relative_to(project_root)}: {e}", file=sys.stderr)

    print("Cleanup complete.")


if __name__ == "__main__":
    clean()

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "utils"))

from find_quarto import find_quarto


def check_command(cmd: str, name: str) -> bool:
    path = shutil.which(cmd)
    if not path:
        print(f"{name:10} NOT FOUND")
        return False

    try:
        version = subprocess.check_output(
            [cmd, "--version"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        print(f"{name:10} Found: {path}")
        print(f"           Version: {version.splitlines()[0]}")
    except Exception:
        print(f"{name:10} Found: {path}")

    return True


def check_quarto() -> bool:
    path = find_quarto()
    if not path:
        print("Quarto    NOT FOUND")
        return False

    try:
        version = subprocess.check_output(
            [path, "--version"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        print(f"Quarto    Found: {path}")
        print(f"           Version: {version.splitlines()[0]}")
    except Exception:
        print(f"Quarto    Found: {path}")

    return True


def main() -> None:
    print("Checking development environment...\n")
    results = [
        check_command("uv", "uv"),
        check_command("just", "just"),
        check_quarto(),
        check_command("npm", "npm"),
    ]

    print(f"\nPython: {sys.executable}")
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()

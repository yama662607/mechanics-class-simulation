import shutil
import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "utils"))

from find_quarto import find_quarto  # noqa: E402


def check_command(cmd, name):
    path = shutil.which(cmd)
    if path:
        try:
            version = (
                subprocess.check_output([cmd, "--version"], stderr=subprocess.STDOUT)
                .decode()
                .strip()
            )
            print(f" {name:10} Found: {path}")
            print(f"   Version: {version.splitlines()[0]}")
            return True
        except Exception:
            print(f" {name:10} Found at {path}, but failed to get version.")
            return True
    else:
        print(f" {name:10} NOT FOUND. Please install it.")
        return False


def check_quarto():
    """Check for Quarto using the enhanced finder (supports fallback paths)."""
    path = find_quarto()
    if path:
        try:
            version = (
                subprocess.check_output([path, "--version"], stderr=subprocess.STDOUT)
                .decode()
                .strip()
            )
            print(f" {'Quarto':10} Found: {path}")
            print(f"   Version: {version.splitlines()[0]}")
            return True
        except Exception:
            print(f" {'Quarto':10} Found at {path}, but failed to get version.")
            return True
    else:
        print(f" {'Quarto':10} NOT FOUND. Please install it.")
        return False


def main():
    print(" Checking development environment...\n")

    results = [
        check_command("uv", "uv"),
        check_command("just", "just"),
        check_quarto(),
        check_command("npm", "Node/npm"),
    ]

    print("\n--- Python Environment ---")
    print(f"Interpretor: {sys.executable}")

    if all(results):
        print("\n All systems go! You are ready to develop.")
        sys.exit(0)
    else:
        print(
            "\n Some dependencies are missing. Please refer to README.md for installation instructions."
        )
        if sys.platform == "win32":
            print("\n WINDOWS TIP:")
            print("   If you just installed these tools, your terminal might not see them yet.")
            print("   Try restarting your terminal (PowerShell/Command Prompt).")
            print("   (Winget and installs often require a fresh session to update PATH)")
        sys.exit(1)


if __name__ == "__main__":
    main()

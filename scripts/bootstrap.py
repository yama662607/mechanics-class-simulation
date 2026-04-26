#!/usr/bin/env python3
"""Bootstrap the development environment from a fresh machine.

Installs (if missing): just, uv, quarto, node, then runs `uv sync` and
`npm install`. After this finishes, `just docs` should work.

Usage:
  python3 scripts/bootstrap.py              # detect OS, install everything
  python3 scripts/bootstrap.py --dry-run    # print what would happen
  python3 scripts/bootstrap.py --skip-deps  # only install tools, skip uv sync / npm install

Exit codes:
  0 — everything (or only the parts you asked for) succeeded
  1 — at least one tool install or dep step failed (see stderr summary)

This file is the shared implementation. The thin OS-specific entry points
(`scripts/bootstrap.sh`, `scripts/bootstrap.ps1`) just locate Python and
re-exec this script. They forward the exit code.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Tool catalogue
# ---------------------------------------------------------------------------
TOOLS = ["just", "uv", "quarto", "node"]


def _is_installed(cmd: str) -> bool:
    return shutil.which(cmd) is not None


# Step records — collected then summarised at the end so partial failure
# is visible (no silent fail).
_failures: list[str] = []


def _run(label: str, cmd: list[str] | str, *, dry: bool, shell: bool = False) -> bool:
    pretty = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"  $ {pretty}")
    if dry:
        return True
    rc = subprocess.call(cmd, shell=shell)
    if rc != 0:
        msg = f"[{label}] failed with exit code {rc}: {pretty}"
        print(msg, file=sys.stderr)
        _failures.append(msg)
        return False
    return True


def _manual(label: str, message: str) -> None:
    """Record a tool that we can't auto-install on this platform."""
    msg = f"[{label}] manual install required:\n    {message}"
    print(msg, file=sys.stderr)
    _failures.append(msg)


# ---------------------------------------------------------------------------
# Per-OS install strategies
# ---------------------------------------------------------------------------


def install_macos(missing: list[str], dry: bool) -> None:
    if not _is_installed("brew"):
        _manual(
            "brew",
            "Homebrew not found. Install it first: "
            '/bin/bash -c "$(curl -fsSL '
            'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
        )
        return
    formula_map = {
        "just": ["brew", "install", "just"],
        "uv": ["brew", "install", "uv"],
        "quarto": ["brew", "install", "--cask", "quarto"],
        "node": ["brew", "install", "node"],
    }
    for tool in missing:
        _run(tool, formula_map[tool], dry=dry)


def _linux_pm() -> str | None:
    for pm in ("apt-get", "dnf", "pacman", "zypper", "apk"):
        if _is_installed(pm):
            return pm
    return None


def install_linux(missing: list[str], dry: bool) -> None:
    """Try the native package manager, then fall back to upstream curl
    installers. Quarto has no curl-pipe installer — point at the .deb/.rpm
    URL when no PM is available."""
    pm = _linux_pm()

    for tool in missing:
        if tool == "uv":
            _run(
                "uv",
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                dry=dry,
                shell=True,
            )
        elif tool == "node":
            if pm == "apt-get":
                _run(
                    "node",
                    "sudo apt-get update && sudo apt-get install -y nodejs npm",
                    dry=dry,
                    shell=True,
                )
            elif pm == "dnf":
                _run("node", ["sudo", "dnf", "install", "-y", "nodejs", "npm"], dry=dry)
            elif pm == "pacman":
                _run(
                    "node",
                    ["sudo", "pacman", "-S", "--noconfirm", "nodejs", "npm"],
                    dry=dry,
                )
            elif pm == "zypper":
                _run("node", ["sudo", "zypper", "install", "-y", "nodejs", "npm"], dry=dry)
            elif pm == "apk":
                _run("node", ["sudo", "apk", "add", "--no-cache", "nodejs", "npm"], dry=dry)
            else:
                _manual("node", "Install Node.js 20+ from https://nodejs.org/")
        elif tool == "just":
            if pm == "pacman":
                _run("just", ["sudo", "pacman", "-S", "--noconfirm", "just"], dry=dry)
            else:
                # Official prebuilt-binary installer — works on glibc and musl.
                _run(
                    "just",
                    "curl --proto '=https' --tlsv1.2 -sSf "
                    "https://just.systems/install.sh | bash -s -- --to ~/.local/bin",
                    dry=dry,
                    shell=True,
                )
                print("  reminder: ensure ~/.local/bin is on $PATH")
        elif tool == "quarto":
            # Quarto has no curl-pipe install path; document the manual step
            # but record it as a failure so the caller knows action is needed.
            _manual(
                "quarto",
                "Quarto on Linux requires a manual download. Get the .deb / .rpm "
                "matching your distro from https://quarto.org/docs/get-started/ — "
                "or install via mise / asdf with a community plugin.",
            )


def install_windows(missing: list[str], dry: bool) -> None:
    """Prefer winget → scoop. Record manual install when neither is available."""
    have_winget = _is_installed("winget")
    have_scoop = _is_installed("scoop")

    winget_ids = {
        "just": "Casey.Just",
        "uv": "astral-sh.uv",
        "quarto": "Posit.Quarto",
        "node": "OpenJS.NodeJS.LTS",
    }
    scoop_pkgs = {
        "just": "just",
        "uv": "uv",
        "quarto": "quarto",
        "node": "nodejs-lts",
    }
    for tool in missing:
        if have_winget:
            _run(
                tool,
                ["winget", "install", "--id", winget_ids[tool], "-e", "--silent"],
                dry=dry,
            )
        elif have_scoop:
            _run(tool, ["scoop", "install", scoop_pkgs[tool]], dry=dry)
        else:
            _manual(
                tool,
                "Neither winget nor scoop found. Install manually:\n"
                "      just  → https://github.com/casey/just/releases\n"
                "      uv    → https://docs.astral.sh/uv/getting-started/installation/\n"
                "      quarto→ https://quarto.org/docs/get-started/\n"
                "      node  → https://nodejs.org/",
            )
            return


# ---------------------------------------------------------------------------
# Project deps
# ---------------------------------------------------------------------------


def install_project_deps(dry: bool) -> None:
    print("\n--- Project dependencies ---")
    if _is_installed("uv"):
        _run("uv sync", ["uv", "sync"], dry=dry)
    else:
        _manual(
            "uv sync",
            "uv not on PATH yet. Restart your shell and re-run `python3 "
            "scripts/bootstrap.py` (or `uv sync` directly).",
        )
    if _is_installed("npm"):
        _run("npm install", ["npm", "install"], dry=dry)
    else:
        _manual(
            "npm install",
            "node/npm not on PATH yet. Restart your shell and re-run, or "
            "run `npm install` directly.",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description="Bootstrap the dev environment.")
    p.add_argument("--dry-run", action="store_true", help="Print commands without executing.")
    p.add_argument(
        "--skip-deps",
        action="store_true",
        help="Install tools only; skip `uv sync` and `npm install`.",
    )
    args = p.parse_args()

    print(f"Project root: {ROOT}")
    print(f"Platform    : {sys.platform}")

    missing = [t for t in TOOLS if not _is_installed(t)]
    if missing:
        print(f"Missing     : {', '.join(missing)}")
    else:
        print("All required tools already installed.")

    if missing:
        print("\n--- Installing missing tools ---")
        if sys.platform == "darwin":
            install_macos(missing, args.dry_run)
        elif sys.platform.startswith("linux"):
            install_linux(missing, args.dry_run)
        elif sys.platform == "win32":
            install_windows(missing, args.dry_run)
        else:
            _manual("platform", f"Unsupported platform: {sys.platform}")

    if not args.skip_deps:
        install_project_deps(args.dry_run)

    print("\n=== Summary ===")
    if not _failures:
        print("All steps succeeded. Restart your shell if PATH changes were made, then:")
        print("  just check-env")
        print("  just docs")
        return 0

    print(f"{len(_failures)} step(s) need attention:", file=sys.stderr)
    for f in _failures:
        print(f"  - {f}", file=sys.stderr)
    print(
        "\nFix the items above (often: install Quarto manually, or restart "
        "your shell so PATH picks up new tools), then re-run this script.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

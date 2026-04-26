"""Cross-platform helper to terminate lingering Quarto preview processes.

Replaces the Unix-only `lsof | xargs kill` / `pkill` idiom in Justfile so the
template works on Windows / macOS / Linux.

Usage: ``uv run python tools/kill_quarto_process.py [--port 4312]``
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from collections.abc import Iterable


def _iter_pids_listening_on(port: int) -> Iterable[int]:
    """Yield PIDs holding a TCP listener on *port*.

    Uses ``psutil`` if available (true cross-platform), otherwise falls back to
    platform-native CLIs (``lsof`` on POSIX, ``netstat`` on Windows).
    """
    try:
        import psutil  # type: ignore
    except ImportError:
        psutil = None  # noqa: N806

    if psutil is not None:
        # Two-tier strategy:
        # 1. Try the cheap system-wide query first (works on Linux/Win
        #    without root, fast even with many processes).
        # 2. If the OS denies that (macOS without root), fall back to
        #    per-process iteration which only needs access to processes
        #    you own.
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.laddr and conn.laddr.port == port and conn.pid:
                    yield conn.pid
            return
        except (psutil.AccessDenied, PermissionError):
            pass

        for proc in psutil.process_iter(["pid"]):
            try:
                for conn in proc.net_connections(kind="inet"):
                    if conn.laddr and conn.laddr.port == port:
                        yield proc.info["pid"]
                        break
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        return

    if os.name == "nt":
        try:
            out = subprocess.check_output(
                ["netstat", "-ano", "-p", "TCP"], text=True, errors="ignore"
            )
        except (OSError, subprocess.CalledProcessError):
            return
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[0] == "TCP" and parts[3] == "LISTENING":
                local = parts[1]
                if local.endswith(f":{port}"):
                    try:
                        yield int(parts[4])
                    except ValueError:
                        pass
    else:
        try:
            out = subprocess.check_output(
                ["lsof", "-ti", f"tcp:{port}"], text=True, errors="ignore"
            )
        except (OSError, subprocess.CalledProcessError):
            return
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit():
                yield int(line)


def _kill(pid: int) -> bool:
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    try:
        os.kill(pid, signal.SIGKILL)  # type: ignore[attr-defined]
        return True
    except ProcessLookupError:
        return True
    except OSError:
        return False


def _kill_by_cmdline(needle: str) -> int:
    """Kill processes whose command line contains *needle*. Requires psutil."""
    try:
        import psutil  # type: ignore
    except ImportError:
        return 0

    killed = 0
    for proc in psutil.process_iter(["pid", "cmdline"]):
        cmdline = proc.info.get("cmdline") or []
        if any(needle in part for part in cmdline):
            if _kill(proc.info["pid"]):
                killed += 1
    return killed


def main() -> int:
    parser = argparse.ArgumentParser(description="Kill lingering Quarto preview processes.")
    parser.add_argument(
        "--port", type=int, default=4312, help="Preview port to free (default: 4312)"
    )
    args = parser.parse_args()

    pids = sorted(set(_iter_pids_listening_on(args.port)))
    for pid in pids:
        ok = _kill(pid)
        print(f"  port {args.port}: pid {pid} {'killed' if ok else 'failed'}")

    extra = _kill_by_cmdline("quarto preview")
    if extra:
        print(f"  killed {extra} stray 'quarto preview' process(es)")

    if not pids and not extra:
        print(f"  no process holding port {args.port} or matching 'quarto preview'")
    return 0


if __name__ == "__main__":
    sys.exit(main())

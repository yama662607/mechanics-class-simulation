"""Find the Quarto CLI binary."""

import shutil
from pathlib import Path

_FALLBACK_PATHS = [
    Path("/Applications/quarto/bin/quarto"),
    Path.home() / ".local" / "bin" / "quarto",
    Path("/opt/quarto/bin/quarto"),
    Path("/usr/local/bin/quarto"),
]


def find_quarto() -> str | None:
    path = shutil.which("quarto")
    if path:
        return path

    for candidate in _FALLBACK_PATHS:
        if candidate.is_file():
            return str(candidate)

    return None

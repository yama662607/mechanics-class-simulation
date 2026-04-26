"""Resolve the path to the Quarto CLI binary.

Quarto may be installed via Homebrew, the official installer, or a manual
download.  On macOS the official `.pkg` installer places the binary under
``/Applications/quarto/bin/quarto``, which is *not* on the default ``PATH``.

This module provides :func:`find_quarto` which first checks ``PATH`` (via
:func:`shutil.which`) and, if that fails, probes well-known installation
locations so that the rest of the tooling can locate the binary without
requiring the user to modify their shell profile.
"""

import shutil
from pathlib import Path

# Well-known fallback locations (checked in order).
_FALLBACK_PATHS = [
    Path("/Applications/quarto/bin/quarto"),
    Path.home() / ".local" / "bin" / "quarto",
    Path("/opt/quarto/bin/quarto"),
    Path("/usr/local/bin/quarto"),
]


def find_quarto() -> str | None:
    """Return the absolute path to the ``quarto`` binary, or ``None``.

    The function first queries ``PATH`` and then falls back to several
    well-known installation directories.
    """
    path = shutil.which("quarto")
    if path:
        return path

    for candidate in _FALLBACK_PATHS:
        if candidate.is_file():
            return str(candidate)

    return None

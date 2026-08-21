"""Open local paths in the host file manager (cross-platform)."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


def open_in_file_manager(path: Path) -> None:
    """Reveal *path* in the desktop file manager.

    Uses ``xdg-open`` (Linux), ``open`` (macOS), or ``os.startfile`` (Windows).
    Raises ``FileNotFoundError`` if the directory does not exist, or
    ``RuntimeError`` if the opener is missing or fails.
    """
    resolved = path.resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"Directory not found: {resolved}")

    system = platform.system()
    if system == "Windows":
        os.startfile(resolved)  # type: ignore[attr-defined]
        return

    if system == "Darwin":
        cmd = ["open", str(resolved)]
    else:
        opener = shutil.which("xdg-open")
        if not opener:
            raise RuntimeError("No file manager opener found (xdg-open)")
        cmd = [opener, str(resolved)]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        message = "Failed to open folder in file manager"
        if detail:
            message = f"{message}: {detail}"
        raise RuntimeError(message)

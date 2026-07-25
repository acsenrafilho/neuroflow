"""Open local paths in the host file manager (Linux xdg-open)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def open_in_file_manager(path: Path) -> None:
    """Reveal *path* in the desktop file manager.

    Uses ``xdg-open`` (Linux). Raises ``FileNotFoundError`` if the directory
    does not exist, or ``RuntimeError`` if the opener is missing or fails.
    """
    resolved = path.resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"Directory not found: {resolved}")

    opener = shutil.which("xdg-open")
    if not opener:
        raise RuntimeError("xdg-open was not found on PATH")

    result = subprocess.run(
        [opener, str(resolved)],
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

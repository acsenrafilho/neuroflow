"""User notification helpers for the Windows launcher."""

from __future__ import annotations

import sys


def notify_user(title: str, body: str) -> None:
    """Show a Windows message box when on win32; no-op elsewhere."""
    if sys.platform != "win32":
        return

    import ctypes

    ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
        None,
        body,
        title,
        0,
    )

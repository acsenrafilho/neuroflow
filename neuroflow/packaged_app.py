"""PyInstaller entrypoint: start the portal and open the browser."""

from __future__ import annotations

import atexit
import contextlib
import os
import threading
import webbrowser
from pathlib import Path

import uvicorn
from rich.console import Console

from neuroflow.runtime_paths import apply_frozen_defaults

console = Console()

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000

_SKIP_BROWSER_VALUES = frozenset({"1", "true", "yes"})
_PIDFILE_ENV = "NEUROFLOW_PORTAL_PIDFILE"


def _skip_browser() -> bool:
    raw = os.environ.get("NEUROFLOW_SKIP_BROWSER", "").strip().lower()
    return raw in _SKIP_BROWSER_VALUES


def _write_portal_pidfile() -> None:
    """Write this process PID when ``NEUROFLOW_PORTAL_PIDFILE`` is set (WSL launcher)."""
    raw = os.environ.get(_PIDFILE_ENV, "").strip()
    if not raw:
        return
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{os.getpid()}\n", encoding="utf-8")

    def _unlink() -> None:
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)

    atexit.register(_unlink)


def main() -> None:
    """Serve the API + UI without reload (packaged end-user mode)."""
    apply_frozen_defaults()
    _write_portal_pidfile()
    host = _DEFAULT_HOST
    port = _DEFAULT_PORT
    url = f"http://{host}:{port}/"

    console.print(f"[bold]NeuroFlow[/bold] → {url}")
    if not _skip_browser():

        def _open_browser() -> None:
            webbrowser.open(url)

        threading.Timer(1.0, _open_browser).start()

    uvicorn.run(
        "neuroflow.api.main:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()

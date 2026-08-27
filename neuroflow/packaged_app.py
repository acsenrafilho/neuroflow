"""PyInstaller entrypoint: start the portal and open the browser."""

from __future__ import annotations

import os
import threading
import webbrowser

import uvicorn
from rich.console import Console

from neuroflow.runtime_paths import apply_frozen_defaults

console = Console()

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000

_SKIP_BROWSER_VALUES = frozenset({"1", "true", "yes"})


def _skip_browser() -> bool:
    raw = os.environ.get("NEUROFLOW_SKIP_BROWSER", "").strip().lower()
    return raw in _SKIP_BROWSER_VALUES


def main() -> None:
    """Serve the API + UI without reload (packaged end-user mode)."""
    apply_frozen_defaults()
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

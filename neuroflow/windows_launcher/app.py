"""CLI entry for the Windows WSL launcher (Phase 1: detection only)."""

from __future__ import annotations

import argparse
import webbrowser

from rich.console import Console

from neuroflow.windows_launcher.detect import probe_wsl
from neuroflow.windows_launcher.notify import notify_user
from neuroflow.windows_launcher.types import WSL_INSTALL_URL, WslState

console = Console()


def _print_probe(probe, *, include_state_line: bool) -> None:
    if include_state_line:
        console.print(f"state={probe.state.value}")
    console.print(probe.message)
    console.print(f"\nMicrosoft WSL guide: {probe.microsoft_url}")


def _handle_default(probe) -> int:
    ready_states = {WslState.UBUNTU_STOPPED, WslState.UBUNTU_RUNNING}
    if probe.state in ready_states:
        _print_probe(probe, include_state_line=False)
        return 0

    _print_probe(probe, include_state_line=False)
    notify_user("NeuroFlow — WSL required", probe.message)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the launcher CLI (detection gate only in Phase 1)."""
    parser = argparse.ArgumentParser(
        prog="NeuroFlow",
        description="NeuroFlow Windows launcher — WSL detection (Phase 1)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print detection state and exit",
    )
    parser.add_argument(
        "--open-wsl-docs",
        action="store_true",
        help="Open the official Microsoft WSL install guide in a browser",
    )
    args = parser.parse_args(argv)

    if args.open_wsl_docs:
        webbrowser.open(WSL_INSTALL_URL)
        console.print(WSL_INSTALL_URL)
        return 0

    try:
        probe = probe_wsl()
    except Exception as exc:  # noqa: BLE001 — top-level launcher safety net
        console.print(f"[red]Unexpected error:[/red] {exc}")
        return 1

    if args.status:
        _print_probe(probe, include_state_line=True)
        return 0

    return _handle_default(probe)


if __name__ == "__main__":
    raise SystemExit(main())

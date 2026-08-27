"""CLI entry for the Windows WSL launcher (detect + runtime + stop)."""

from __future__ import annotations

import argparse
import webbrowser

from rich.console import Console

from neuroflow.windows_launcher.arch import windows_is_arm, windows_machine_arch
from neuroflow.windows_launcher.detect import probe_wsl
from neuroflow.windows_launcher.messages import MSG_ARM_REFUSED
from neuroflow.windows_launcher.notify import notify_user
from neuroflow.windows_launcher.runtime import launch
from neuroflow.windows_launcher.stop import stop_portal
from neuroflow.windows_launcher.types import WSL_INSTALL_URL, WslState

console = Console()

_READY_STATES = frozenset({WslState.UBUNTU_STOPPED, WslState.UBUNTU_RUNNING})


def _print_probe(probe, *, include_state_line: bool, arch: str | None = None) -> None:
    if include_state_line:
        console.print(f"state={probe.state.value}")
        if arch is not None and arch != "x86_64":
            console.print(f"arch={arch}")
    console.print(probe.message)
    console.print(f"\nMicrosoft WSL guide: {probe.microsoft_url}")


def _handle_default(probe) -> int:
    if probe.state in _READY_STATES:
        return launch(probe)

    _print_probe(probe, include_state_line=False)
    notify_user("NeuroFlow — WSL required", probe.message)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the launcher CLI (detection gate + portal runtime + stop)."""
    parser = argparse.ArgumentParser(
        prog="NeuroFlow",
        description="NeuroFlow Windows launcher — WSL detection and portal start",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print detection state and exit",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the Linux portal (does not run wsl --shutdown)",
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

    win_arch = windows_machine_arch()

    # --status always probes; print arch when not x86_64 (support diagnostics).
    if args.status:
        try:
            probe = probe_wsl()
        except Exception as exc:  # noqa: BLE001 — top-level launcher safety net
            console.print(f"[red]Unexpected error:[/red] {exc}")
            return 1
        _print_probe(probe, include_state_line=True, arch=win_arch)
        return 0

    # ARM Windows: refuse default launch (and --stop has nothing useful to do).
    if windows_is_arm():
        if args.stop:
            console.print(MSG_ARM_REFUSED)
            return 0
        console.print(MSG_ARM_REFUSED)
        notify_user("NeuroFlow — unsupported architecture", MSG_ARM_REFUSED)
        return 0

    try:
        probe = probe_wsl()
    except Exception as exc:  # noqa: BLE001 — top-level launcher safety net
        console.print(f"[red]Unexpected error:[/red] {exc}")
        return 1

    if args.stop:
        return stop_portal(probe)

    return _handle_default(probe)


if __name__ == "__main__":
    raise SystemExit(main())

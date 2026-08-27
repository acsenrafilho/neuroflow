"""Orchestrate copy → start → health poll → browser for ready Ubuntu states.

Maintainer dogfood (same layout as the release zip):
1. On Linux, build the onedir: ``packaging/build_release.sh`` → ``dist/neuroflow/``.
2. On Windows, place that folder as ``linux-payload/`` next to the launcher, or set
   ``NEUROFLOW_LINUX_PAYLOAD`` to it.
3. Run: ``poetry run python -m neuroflow.windows_launcher_app`` (with WSL2 Ubuntu ready).
"""

from __future__ import annotations

import subprocess
import webbrowser

from rich.console import Console

from neuroflow.windows_launcher.detect import WslProbe
from neuroflow.windows_launcher.health import HealthStatus, probe_health, wait_until_healthy
from neuroflow.windows_launcher.host_scan import choose_landing_url
from neuroflow.windows_launcher.messages import (
    MSG_HEALTH_TIMEOUT,
    MSG_HOST_TOOLS_MISSING,
    MSG_PAYLOAD_MISSING,
    MSG_PORT_BUSY,
    MSG_RUNNING,
    MSG_START_FAILED,
    MSG_WAKE_FAILED,
)
from neuroflow.windows_launcher.notify import notify_user
from neuroflow.windows_launcher.payload import PayloadError, ensure_payload_installed
from neuroflow.windows_launcher.types import WslState
from neuroflow.windows_launcher.wsl_exec import (
    DISTRO,
    WSL_WAKE_TIMEOUT_SECONDS,
    popen_wsl,
    run_wsl,
)

console = Console()

_READY = frozenset({WslState.UBUNTU_STOPPED, WslState.UBUNTU_RUNNING})


def _fail(title: str, body: str, *, code: int = 1) -> int:
    console.print(f"[red]{body}[/red]")
    notify_user(title, body)
    return code


def _open_portal_browser() -> None:
    """Open Home or Host tools help based on portal package readiness."""
    url, all_missing = choose_landing_url()
    if all_missing:
        console.print(MSG_HOST_TOOLS_MISSING)
    webbrowser.open(url)
    console.print(f"Opened browser at {url}")


def _wake_ubuntu(wsl_exe: str) -> bool:
    try:
        result = run_wsl(
            wsl_exe,
            ["-d", DISTRO, "--", "true"],
            timeout=WSL_WAKE_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


def launch(probe: WslProbe, *, wait_on_process: bool = True) -> int:
    """Run the Phase 2 happy path for a ready Ubuntu probe result.

    Parameters
    ----------
    wait_on_process:
        When True (default double-click), block on the WSL portal process after
        opening the browser. Tests may set False after health succeeds.
    """
    if probe.state not in _READY:
        raise ValueError(f"launch() requires a ready state, got {probe.state}")
    if not probe.wsl_exe:
        return _fail("NeuroFlow", "WSL executable path is missing.")

    wsl_exe = probe.wsl_exe

    # Idempotent: portal already up → browser only.
    existing = probe_health()
    if existing.status == HealthStatus.OK:
        _open_portal_browser()
        return 0
    if existing.status == HealthStatus.PORT_BUSY:
        return _fail("NeuroFlow — port busy", MSG_PORT_BUSY)

    if probe.state == WslState.UBUNTU_STOPPED:
        console.print("Starting Ubuntu…")
        if not _wake_ubuntu(wsl_exe):
            return _fail("NeuroFlow — Ubuntu", MSG_WAKE_FAILED)

    try:
        paths = ensure_payload_installed(wsl_exe)
    except PayloadError as exc:
        detail = str(exc)
        lowered = detail.lower()
        if "not found" in lowered or "missing" in lowered:
            body = MSG_PAYLOAD_MISSING
        else:
            body = f"{MSG_START_FAILED}\n\n{detail}"
        return _fail("NeuroFlow — payload", body)

    console.print(f"Starting Linux portal at {paths.linux_elf}…")
    try:
        proc = popen_wsl(
            wsl_exe,
            [
                "-d",
                DISTRO,
                "--",
                "env",
                "NEUROFLOW_SKIP_BROWSER=1",
                paths.linux_elf,
            ],
            linux_home=paths.linux_home,
        )
    except OSError as exc:
        return _fail("NeuroFlow — start failed", f"{MSG_START_FAILED}\n\n{exc}")

    health = wait_until_healthy()
    if health.status == HealthStatus.OK:
        console.print(MSG_RUNNING)
        _open_portal_browser()
        if wait_on_process:
            return int(proc.wait() or 0)
        return 0

    if health.status == HealthStatus.PORT_BUSY:
        # Avoid leaving a half-started portal hanging when possible.
        proc.terminate()
        return _fail("NeuroFlow — port busy", MSG_PORT_BUSY)

    proc.terminate()
    extra = f"\n\n({health.detail})" if health.detail else ""
    return _fail("NeuroFlow — health timeout", f"{MSG_HEALTH_TIMEOUT}{extra}")

"""Stop the Linux portal via the pidfile under ~/.neuroflow-app/."""

from __future__ import annotations

import time
from collections.abc import Callable

from rich.console import Console

from neuroflow.windows_launcher.detect import WslProbe, decode_wsl_output
from neuroflow.windows_launcher.health import HealthStatus, probe_health
from neuroflow.windows_launcher.messages import (
    MSG_NOT_RUNNING,
    MSG_STOP_DONE,
    MSG_STOP_NO_PIDFILE,
    MSG_STOP_PARTIAL,
)
from neuroflow.windows_launcher.types import WslState
from neuroflow.windows_launcher.wsl_exec import (
    DISTRO,
    WSL_PROBE_TIMEOUT_SECONDS,
    WSL_STOP_TIMEOUT_SECONDS,
    portal_pidfile_path,
    run_wsl,
)

console = Console()

STOP_HEALTH_BUDGET_SECONDS = 10.0
STOP_HEALTH_INTERVAL_SECONDS = 0.4

_NOT_RUNNING_STATES = frozenset(
    {
        WslState.WSL_MISSING,
        WslState.WSL_PRESENT_NO_UBUNTU,
        WslState.UBUNTU_STOPPED,
        WslState.UBUNTU_NEEDS_USER_SETUP,
    }
)


def _parse_pid(raw: str) -> int | None:
    text = raw.strip()
    if not text.isdigit():
        return None
    pid = int(text)
    if pid <= 1:
        return None
    return pid


def _wait_until_unhealthy(
    *,
    budget_seconds: float = STOP_HEALTH_BUDGET_SECONDS,
    interval_seconds: float = STOP_HEALTH_INTERVAL_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """Return True when health is no longer OK within the budget."""
    deadline = time.monotonic() + budget_seconds
    while time.monotonic() < deadline:
        if probe_health().status != HealthStatus.OK:
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        sleep(min(interval_seconds, remaining))
    return probe_health().status != HealthStatus.OK


def stop_portal(probe: WslProbe) -> int:
    """Stop the Linux portal recorded in ``~/.neuroflow-app/portal.pid``.

    Never calls ``wsl --shutdown``. Does not kill neuroimaging job processes
    (they use separate sessions). Never wakes a stopped Ubuntu just to stop.
    """
    if probe.state in _NOT_RUNNING_STATES or not probe.wsl_exe:
        console.print(MSG_NOT_RUNNING)
        return 0

    wsl_exe = probe.wsl_exe
    home_result = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "printenv", "HOME"],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
    )
    linux_home = decode_wsl_output(home_result.stdout or b"").strip()
    if home_result.returncode != 0 or not linux_home.startswith("/"):
        console.print(MSG_NOT_RUNNING)
        return 0

    pidfile = portal_pidfile_path(linux_home)
    exists = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "test", "-f", pidfile],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
        linux_home=linux_home,
    )
    if exists.returncode != 0:
        health = probe_health()
        if health.status == HealthStatus.OK:
            console.print(MSG_STOP_NO_PIDFILE)
        else:
            console.print(MSG_NOT_RUNNING)
        return 0

    cat = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "cat", pidfile],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
        linux_home=linux_home,
    )
    pid = _parse_pid(decode_wsl_output(cat.stdout or b""))
    if cat.returncode != 0 or pid is None:
        health = probe_health()
        if health.status == HealthStatus.OK:
            console.print(MSG_STOP_NO_PIDFILE)
        else:
            console.print(MSG_NOT_RUNNING)
        return 0

    run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "kill", "-TERM", str(pid)],
        timeout=WSL_STOP_TIMEOUT_SECONDS,
        linux_home=linux_home,
    )

    if not _wait_until_unhealthy():
        run_wsl(
            wsl_exe,
            ["-d", DISTRO, "--", "kill", "-KILL", str(pid)],
            timeout=WSL_STOP_TIMEOUT_SECONDS,
            linux_home=linux_home,
        )
        run_wsl(
            wsl_exe,
            ["-d", DISTRO, "--", "rm", "-f", pidfile],
            timeout=WSL_PROBE_TIMEOUT_SECONDS,
            linux_home=linux_home,
        )
        _wait_until_unhealthy(budget_seconds=3.0)

    if probe_health().status == HealthStatus.OK:
        console.print(MSG_STOP_PARTIAL)
        return 1

    console.print(MSG_STOP_DONE)
    return 0

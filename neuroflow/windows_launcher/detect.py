"""WSL2 / Ubuntu detection for the Windows launcher."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from neuroflow.windows_launcher.messages import message_for_state
from neuroflow.windows_launcher.types import WSL_INSTALL_URL, WslState
from neuroflow.windows_launcher.wsl_exec import (
    DISTRO,
    WSL_LIST_TIMEOUT_SECONDS,
    WSL_PROBE_TIMEOUT_SECONDS,
    DisallowedWslArgumentError,
    run_wsl,
    validate_wsl_argv,
)

# Re-export for callers/tests that imported from detect.
__all__ = [
    "DisallowedWslArgumentError",
    "WslProbe",
    "decode_wsl_output",
    "probe_wsl",
    "validate_wsl_argv",
]

_DISTRO_LINE = re.compile(
    r"^(?P<default>\*?)\s*(?P<name>\S+)\s+(?P<state>Running|Stopped)\s+(?P<version>\d+)\s*$"
)

_WSL_NOT_INSTALLED_MARKERS = (
    "windows subsystem for linux has no installed distributions",
    "the windows subsystem for linux is not installed",
    "wsl is not installed",
    "please enable the virtual machine platform",
    "wsl 2 requires an update",
)


@dataclass(frozen=True)
class WslProbe:
    """Result of WSL/Ubuntu detection."""

    state: WslState
    wsl_exe: str | None
    distro: str | None
    wsl_version: int | None
    microsoft_url: str
    message: str


def decode_wsl_output(raw: bytes) -> str:
    """Decode wsl.exe stdout/stderr (UTF-16 LE is common on Windows)."""
    if not raw:
        return ""

    if raw.startswith(b"\xff\xfe"):
        text = raw[2:].decode("utf-16-le", errors="replace")
    elif raw.startswith(b"\xfe\xff"):
        text = raw[2:].decode("utf-16-be", errors="replace")
    elif len(raw) >= 2 and raw[1:2] == b"\x00":
        text = raw.decode("utf-16-le", errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")

    return text.replace("\r", "").replace("\x00", "").strip()


def _looks_like_wsl_not_installed(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _WSL_NOT_INSTALLED_MARKERS)


def _find_wsl_exe() -> str | None:
    for name in ("wsl", "wsl.exe"):
        found = shutil.which(name)
        if found:
            return found

    if sys.platform != "win32":
        return None

    system_root = os.environ.get("SYSTEMROOT", r"C:\Windows")
    for relative in (
        Path(system_root) / "System32" / "wsl.exe",
        Path(system_root) / "Sysnative" / "wsl.exe",
    ):
        if relative.is_file():
            return str(relative)
    return None


def _run_wsl(wsl_exe: str, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    timeout = (
        WSL_PROBE_TIMEOUT_SECONDS
        if args == ["-d", DISTRO, "--", "true"]
        else WSL_LIST_TIMEOUT_SECONDS
    )
    return run_wsl(wsl_exe, args, timeout=timeout)


def _parse_distro_list(text: str) -> dict[str, tuple[str, int]]:
    """Return {name: (state, version)} from ``wsl -l -v`` output."""
    distros: dict[str, tuple[str, int]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("name"):
            continue
        match = _DISTRO_LINE.match(stripped)
        if match is None:
            continue
        distros[match.group("name")] = (
            match.group("state"),
            int(match.group("version")),
        )
    return distros


def _probe_result(
    state: WslState,
    wsl_exe: str | None,
    distro: str | None = None,
    wsl_version: int | None = None,
) -> WslProbe:
    return WslProbe(
        state=state,
        wsl_exe=wsl_exe,
        distro=distro,
        wsl_version=wsl_version,
        microsoft_url=WSL_INSTALL_URL,
        message=message_for_state(state),
    )


def _ubuntu_running_check(wsl_exe: str) -> WslState:
    try:
        result = _run_wsl(wsl_exe, ["-d", DISTRO, "--", "true"])
    except (subprocess.TimeoutExpired, OSError):
        return WslState.UBUNTU_NEEDS_USER_SETUP
    if result.returncode == 0:
        return WslState.UBUNTU_RUNNING
    return WslState.UBUNTU_NEEDS_USER_SETUP


def probe_wsl() -> WslProbe:
    """Detect WSL and Ubuntu readiness without starting a stopped distro."""
    wsl_exe = _find_wsl_exe()
    if wsl_exe is None:
        return _probe_result(WslState.WSL_MISSING, None)

    try:
        list_result = _run_wsl(wsl_exe, ["-l", "-v"])
    except FileNotFoundError:
        return _probe_result(WslState.WSL_MISSING, wsl_exe)
    except subprocess.TimeoutExpired:
        return _probe_result(WslState.WSL_MISSING, wsl_exe)

    raw = list_result.stdout or list_result.stderr or b""
    text = decode_wsl_output(raw)

    if list_result.returncode != 0 and _looks_like_wsl_not_installed(text):
        return _probe_result(WslState.WSL_MISSING, wsl_exe)

    distros = _parse_distro_list(text)
    if DISTRO not in distros:
        return _probe_result(WslState.WSL_PRESENT_NO_UBUNTU, wsl_exe)

    ubuntu_state, ubuntu_version = distros[DISTRO]
    if ubuntu_state == "Stopped":
        return _probe_result(
            WslState.UBUNTU_STOPPED,
            wsl_exe,
            distro=DISTRO,
            wsl_version=ubuntu_version,
        )

    state = _ubuntu_running_check(wsl_exe)
    return _probe_result(
        state,
        wsl_exe,
        distro=DISTRO,
        wsl_version=ubuntu_version,
    )

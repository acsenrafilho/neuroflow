"""Architecture gates for the Windows WSL launcher (x86_64 only in v1)."""

from __future__ import annotations

import os
import platform
import sys

from neuroflow.windows_launcher.detect import decode_wsl_output
from neuroflow.windows_launcher.wsl_exec import (
    DISTRO,
    WSL_PROBE_TIMEOUT_SECONDS,
    run_wsl,
)

_ARM_MARKERS = frozenset({"arm64", "aarch64", "armv8", "armv8l"})
_X86_MARKERS = frozenset({"amd64", "x86_64", "x64", "i386", "i686", "x86"})


def normalize_arch(raw: str) -> str:
    """Normalize a machine/architecture string to a short token."""
    token = raw.strip().lower().replace("-", "_")
    if token in _ARM_MARKERS or "arm64" in token or "aarch64" in token:
        return "arm64"
    if token in _X86_MARKERS:
        return "x86_64"
    return token or "unknown"


def is_arm_arch(raw: str) -> bool:
    """Return True when *raw* looks like ARM64 / aarch64."""
    return normalize_arch(raw) == "arm64"


def windows_machine_arch() -> str:
    """Detect the Windows host architecture (not the Ubuntu guest)."""
    # WOW64: 32-bit process on 64-bit OS — prefer the native arch env vars.
    for key in ("PROCESSOR_ARCHITEW6432", "PROCESSOR_ARCHITECTURE"):
        value = os.environ.get(key, "").strip()
        if value:
            return normalize_arch(value)
    return normalize_arch(platform.machine() or sys.platform)


def windows_is_arm() -> bool:
    """Return True when the Windows host is ARM64."""
    return windows_machine_arch() == "arm64"


def probe_ubuntu_arch(wsl_exe: str) -> str:
    """Run ``uname -m`` inside Ubuntu and return a normalized arch token."""
    result = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "uname", "-m"],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
    )
    text = decode_wsl_output(result.stdout or b"").strip()
    if result.returncode != 0 or not text:
        return "unknown"
    return normalize_arch(text)

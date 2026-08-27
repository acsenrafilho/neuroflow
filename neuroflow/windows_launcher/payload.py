"""Resolve and install the Linux portal onedir into Ubuntu."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from neuroflow import __version__
from neuroflow.windows_launcher.detect import decode_wsl_output
from neuroflow.windows_launcher.wsl_exec import (
    DISTRO,
    WSL_COPY_TIMEOUT_SECONDS,
    WSL_PROBE_TIMEOUT_SECONDS,
    run_wsl,
)

PAYLOAD_ENV = "NEUROFLOW_LINUX_PAYLOAD"
APP_DIR_NAME = ".neuroflow-app"


class PayloadError(Exception):
    """Raised when the Linux payload cannot be resolved or installed."""


@dataclass(frozen=True)
class PayloadPaths:
    """Windows source and Linux destination for the packaged portal."""

    windows_dir: Path
    linux_home: str
    linux_dest: str
    linux_elf: str


def _launcher_dir() -> Path:
    """Directory that contains the launcher executable (or this package in dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # Dogfood: look next to a conventional layout relative to CWD first.
    return Path.cwd()


def resolve_payload_dir(override: str | None = None) -> Path:
    """Locate ``linux-payload`` (or ``NEUROFLOW_LINUX_PAYLOAD``).

    A valid onedir contains an executable named ``neuroflow`` and an
    ``_internal`` directory (PyInstaller COLLECT layout).
    """
    raw = override if override is not None else os.environ.get(PAYLOAD_ENV)
    if raw:
        candidate = Path(raw).expanduser().resolve()
    else:
        candidate = (_launcher_dir() / "linux-payload").resolve()

    if not candidate.is_dir():
        raise PayloadError(
            f"Linux payload not found at {candidate}. "
            f"Place linux-payload/ next to NeuroFlow.exe or set {PAYLOAD_ENV}."
        )

    elf = candidate / "neuroflow"
    internal = candidate / "_internal"
    if not elf.is_file():
        raise PayloadError(f"Linux payload at {candidate} is missing the 'neuroflow' executable.")
    if not internal.is_dir():
        raise PayloadError(f"Linux payload at {candidate} is missing the '_internal' directory.")
    return candidate


def _ubuntu_home(wsl_exe: str) -> str:
    result = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "printenv", "HOME"],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
    )
    home = decode_wsl_output(result.stdout or b"").strip()
    if result.returncode != 0 or not home.startswith("/"):
        raise PayloadError("Could not read the Ubuntu home directory (printenv HOME failed).")
    return home


def install_paths(wsl_exe: str, windows_dir: Path, *, version: str | None = None) -> PayloadPaths:
    """Build source/dest paths for the current NeuroFlow version."""
    ver = version or __version__
    linux_home = _ubuntu_home(wsl_exe)
    linux_dest = f"{linux_home.rstrip('/')}/{APP_DIR_NAME}/{ver}"
    return PayloadPaths(
        windows_dir=windows_dir,
        linux_home=linux_home,
        linux_dest=linux_dest,
        linux_elf=f"{linux_dest}/neuroflow",
    )


def _is_installed(wsl_exe: str, paths: PayloadPaths) -> bool:
    home = paths.linux_home
    elf_ok = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "test", "-x", paths.linux_elf],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
        linux_home=home,
    )
    if elf_ok.returncode != 0:
        return False
    internal_ok = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "test", "-d", f"{paths.linux_dest}/_internal"],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
        linux_home=home,
    )
    return internal_ok.returncode == 0


def _wslpath_unix(wsl_exe: str, windows_path: Path) -> str:
    result = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "wslpath", "-u", str(windows_path)],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
    )
    unix = decode_wsl_output(result.stdout or b"").strip()
    if result.returncode != 0 or not unix.startswith("/"):
        raise PayloadError(f"wslpath failed for {windows_path}")
    return unix


def ensure_payload_installed(
    wsl_exe: str,
    windows_dir: Path | None = None,
    *,
    version: str | None = None,
) -> PayloadPaths:
    """Copy the Linux onedir into ``~/.neuroflow-app/<ver>/`` if needed.

    Always runs ``chmod +x`` after a copy so NTFS→Linux execute bits are set.
    Skips the copy when the ELF and ``_internal`` already exist.
    """
    source = windows_dir if windows_dir is not None else resolve_payload_dir()
    paths = install_paths(wsl_exe, source, version=version)
    home = paths.linux_home

    if _is_installed(wsl_exe, paths):
        return paths

    src_unix = _wslpath_unix(wsl_exe, source)
    mkdir = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "mkdir", "-p", paths.linux_dest],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
        linux_home=home,
    )
    if mkdir.returncode != 0:
        err = decode_wsl_output(mkdir.stderr or mkdir.stdout or b"")
        raise PayloadError(f"mkdir failed for {paths.linux_dest}: {err}")

    copy = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "cp", "-a", f"{src_unix}/.", f"{paths.linux_dest}/"],
        timeout=WSL_COPY_TIMEOUT_SECONDS,
        linux_home=home,
    )
    if copy.returncode != 0:
        err = decode_wsl_output(copy.stderr or copy.stdout or b"")
        raise PayloadError(f"Failed to copy Linux payload into Ubuntu: {err}")

    chmod = run_wsl(
        wsl_exe,
        ["-d", DISTRO, "--", "chmod", "+x", paths.linux_elf],
        timeout=WSL_PROBE_TIMEOUT_SECONDS,
        linux_home=home,
    )
    if chmod.returncode != 0:
        err = decode_wsl_output(chmod.stderr or chmod.stdout or b"")
        raise PayloadError(f"chmod +x failed for {paths.linux_elf}: {err}")

    return paths

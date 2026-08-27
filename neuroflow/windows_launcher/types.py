"""Shared types and constants for the Windows launcher."""

from __future__ import annotations

import enum

WSL_INSTALL_URL = "https://learn.microsoft.com/windows/wsl/install"


class WslState(str, enum.Enum):
    """Outcome of probing WSL and the Ubuntu distribution."""

    WSL_MISSING = "wsl_missing"
    WSL_PRESENT_NO_UBUNTU = "wsl_present_no_ubuntu"
    UBUNTU_STOPPED = "ubuntu_stopped"
    UBUNTU_RUNNING = "ubuntu_running"
    UBUNTU_NEEDS_USER_SETUP = "ubuntu_needs_user_setup"

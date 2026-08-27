"""English copy for WSL detection states."""

from __future__ import annotations

from neuroflow.windows_launcher.types import WSL_INSTALL_URL, WslState

_COMMON_FOOTER = (
    "NeuroFlow does not install WSL for you. Follow Microsoft's guide (admin rights and a "
    "possible restart are required). WSL does not reserve a separate disk partition — the "
    "Ubuntu virtual disk grows as you use it. On first Ubuntu launch, create a Linux "
    "username and password."
)

_MESSAGES: dict[WslState, str] = {
    WslState.WSL_MISSING: (
        "Windows Subsystem for Linux (WSL) is not available on this computer.\n\n"
        f"Install WSL 2 and the Ubuntu distribution using Microsoft's official guide:\n"
        f"{WSL_INSTALL_URL}\n\n"
        f"{_COMMON_FOOTER}"
    ),
    WslState.WSL_PRESENT_NO_UBUNTU: (
        "WSL is installed, but the Ubuntu distribution was not found.\n\n"
        "NeuroFlow requires a WSL 2 distro named exactly \"Ubuntu\".\n\n"
        f"Install Ubuntu from Microsoft's guide:\n{WSL_INSTALL_URL}\n\n"
        f"{_COMMON_FOOTER}"
    ),
    WslState.UBUNTU_STOPPED: (
        "Ubuntu is installed in WSL but is currently stopped.\n\n"
        "NeuroFlow will start Ubuntu automatically in a future release. "
        "For now, open Ubuntu once from the Start menu to finish setup if you have not "
        "already, then run NeuroFlow again."
    ),
    WslState.UBUNTU_RUNNING: (
        "Ubuntu is running in WSL and ready for NeuroFlow.\n\n"
        "Portal start is not included in this build — that arrives in a later phase."
    ),
    WslState.UBUNTU_NEEDS_USER_SETUP: (
        "Ubuntu is installed but may need first-time setup.\n\n"
        "Open \"Ubuntu\" from the Start menu and create your Linux username and password. "
        "Then run NeuroFlow again.\n\n"
        f"If you still see this message, check Microsoft's WSL guide:\n{WSL_INSTALL_URL}"
    ),
}


def message_for_state(state: WslState) -> str:
    """Return the English user-facing message for a detection state."""
    return _MESSAGES[state]

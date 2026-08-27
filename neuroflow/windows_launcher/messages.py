"""English copy for WSL detection and runtime failure states."""

from __future__ import annotations

from neuroflow.windows_launcher.types import (
    PORTAL_URL,
    WSL_INSTALL_URL,
    WSL_LOCALHOST_TROUBLESHOOTING_URL,
    WslState,
)

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
        'NeuroFlow requires a WSL 2 distro named exactly "Ubuntu".\n\n'
        f"Install Ubuntu from Microsoft's guide:\n{WSL_INSTALL_URL}\n\n"
        f"{_COMMON_FOOTER}"
    ),
    WslState.UBUNTU_STOPPED: (
        "Ubuntu is installed in WSL but is currently stopped.\n\n"
        "NeuroFlow will start Ubuntu automatically and open the portal in your browser."
    ),
    WslState.UBUNTU_RUNNING: (
        "Ubuntu is running in WSL and ready for NeuroFlow.\n\n"
        "Starting the Linux portal and opening your browser…"
    ),
    WslState.UBUNTU_NEEDS_USER_SETUP: (
        "Ubuntu is installed but may need first-time setup.\n\n"
        'Open "Ubuntu" from the Start menu and create your Linux username and password. '
        "Then run NeuroFlow again.\n\n"
        f"If you still see this message, check Microsoft's WSL guide:\n{WSL_INSTALL_URL}"
    ),
}

MSG_PAYLOAD_MISSING = (
    "The Linux portal payload was not found.\n\n"
    "Place a linux-payload/ folder next to NeuroFlow.exe "
    "(the same onedir layout as the Linux release: neuroflow + _internal/), "
    "or set the NEUROFLOW_LINUX_PAYLOAD environment variable to that folder.\n\n"
    "Release zips already bundle linux-payload/ next to NeuroFlow.exe — "
    "keep that folder after extract."
)

MSG_PORT_BUSY = (
    f"Port 8000 on {PORTAL_URL} is in use, but NeuroFlow's health check did not succeed.\n\n"
    "Stop the other program using port 8000, then run NeuroFlow again. "
    "NeuroFlow will not kill that process for you."
)

MSG_HEALTH_TIMEOUT = (
    "NeuroFlow started inside Ubuntu, but Windows could not reach "
    f"{PORTAL_URL} in time.\n\n"
    "On Windows 10, WSL2 localhost forwarding can fail. Try opening the URL from inside "
    "Ubuntu first, then see Microsoft's WSL networking guide:\n"
    f"{WSL_LOCALHOST_TROUBLESHOOTING_URL}"
)

MSG_WAKE_FAILED = (
    "Ubuntu could not be started.\n\n"
    'Open "Ubuntu" from the Start menu once to finish setup, then run NeuroFlow again.'
)

MSG_START_FAILED = (
    "NeuroFlow could not start the Linux portal inside Ubuntu.\n\n"
    "Check that linux-payload/ is present and that Ubuntu is ready, then try again."
)

MSG_RUNNING = f"NeuroFlow is running at {PORTAL_URL} — you can minimize this window."

MSG_HOST_TOOLS_MISSING = (
    "FreeSurfer, FSL, and SCT were not found in Ubuntu. "
    "Install them inside Ubuntu (not on the Windows PATH), then use Rescan on the "
    "Host tools help page."
)

MSG_ALREADY_STARTING = (
    "NeuroFlow is already starting in another window.\n\n"
    "Wait a few seconds for the browser to open, or run NeuroFlow again once the "
    "portal is up."
)

MSG_ARM_REFUSED = (
    "This NeuroFlow release supports x86_64 (AMD64) Windows and Ubuntu only.\n\n"
    "ARM Windows / aarch64 WSL is out of scope for v1. Use an x86_64 Windows PC "
    "with WSL2 Ubuntu."
)

MSG_NOT_RUNNING = "NeuroFlow is not running."

MSG_STOP_DONE = (
    f"NeuroFlow stopped. {PORTAL_URL} should no longer respond.\n\n"
    "Note: --stop ends only the portal. Running neuroimaging jobs inside Ubuntu "
    "are not cancelled — use Cancel in the UI first if you need them stopped. "
    "NeuroFlow never runs wsl --shutdown."
)

MSG_STOP_NO_PIDFILE = (
    f"Something is responding at {PORTAL_URL}, but NeuroFlow has no portal.pid "
    "under ~/.neuroflow-app/.\n\n"
    "That process was probably not started by this launcher. Stop it yourself "
    "(or close the other NeuroFlow window). NeuroFlow will not kill unknown "
    "processes on port 8000."
)

MSG_STOP_PARTIAL = (
    "NeuroFlow sent a stop signal, but the health check still succeeds.\n\n"
    "Try again, or close the console window that started NeuroFlow. "
    "NeuroFlow never runs wsl --shutdown."
)


def message_for_state(state: WslState) -> str:
    """Return the English user-facing message for a detection state."""
    return _MESSAGES[state]

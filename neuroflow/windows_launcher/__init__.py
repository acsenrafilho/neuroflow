"""Windows WSL launcher — detection gate (Phase 1)."""

from neuroflow.windows_launcher.detect import WslProbe, probe_wsl
from neuroflow.windows_launcher.types import WSL_INSTALL_URL, WslState

__all__ = [
    "WSL_INSTALL_URL",
    "WslProbe",
    "WslState",
    "probe_wsl",
]

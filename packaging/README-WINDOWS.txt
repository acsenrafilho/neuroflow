NeuroFlow for Windows
=====================

This zip is a thin Windows launcher. Processing runs inside WSL2 Ubuntu, not on
native Windows.

Quick start
-----------

1. Extract this entire folder. Keep NeuroFlow.exe, _internal/, and
   linux-payload/ together — do not delete either folder.
2. Double-click NeuroFlow.exe.
3. If WSL2 or Ubuntu is missing, follow Microsoft's official guide:
   https://learn.microsoft.com/windows/wsl/install
   NeuroFlow never installs WSL, never runs "wsl --install", and never reboots
   your PC for you.
4. After Ubuntu is ready, click NeuroFlow.exe again. Chrome (or your default
   browser) opens http://127.0.0.1:8000/ while the portal runs in Linux.
5. To stop the portal later: NeuroFlow.exe --stop
   (does not run "wsl --shutdown"; does not cancel running jobs).

Requirements
------------

- Windows 11 + WSL2 (primary). Windows 10 + WSL2 works with possible localhost
  caveats.
- Distro name: Ubuntu.
- Architecture: x86_64 only. The launcher refuses ARM Windows / aarch64 Ubuntu.
- FreeSurfer, FSL, and SCT (if you need them) must be installed inside Ubuntu,
  not on the native Windows PATH.

Where data lives
----------------

Jobs and datasets are stored under the Ubuntu home (typically ~/.neuroflow/),
not under C:\Users\... as the primary location.

Host tools
----------

FreeSurfer, FSL, and SCT must be installed inside Ubuntu, not on the native
Windows PATH. If Home shows "Install on host", open Host tools in the app
(http://127.0.0.1:8000/help/host-tools.html), install the packages in Ubuntu,
then click "Rescan host tools". That status is not a Windows PATH bug.

When FreeSurfer, FSL, and SCT are all missing, NeuroFlow.exe may open the Host
tools help page first instead of Home.

SmartScreen
-----------

Unsigned builds may show "Windows protected your PC". Choose
More info → Run anyway when you trust this release.

More help
---------

After the portal starts, open /help/windows-wsl.html or /help/host-tools.html
in the app, or read:
https://neuroflowpipelines.readthedocs.io/en/latest/user/windows-wsl/

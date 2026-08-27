# Windows and WSL

On Windows, NeuroFlow is a **facilitation portal in your browser** while **processing runs in Linux** on WSL2 Ubuntu. You click NeuroFlow on Windows, use the site in Chrome, and jobs execute inside Ubuntu — provided WSL and the neuroimaging tools are already installed. NeuroFlow guides you to official docs; it does not install WSL or vendor CLIs for you.

## Requirements

| Item | Detail |
|------|--------|
| Windows | **Windows 11 + WSL2** is the primary target. Windows 10 + WSL2 is supported; see [Troubleshooting](#troubleshooting) for localhost caveats. |
| Distro | **Ubuntu** (default name). Install Ubuntu from Microsoft’s guide — do not substitute Debian or docker-desktop silently. |
| Architecture | **x86_64** for v1. ARM Windows is out of scope. |
| Browser | Chrome or another browser on Windows at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (WSL2 localhost forwarding on Windows 11). |
| Host tools | FreeSurfer, FSL, SCT, etc. installed **inside Ubuntu**, not on the native Windows PATH. |

## Install WSL yourself

NeuroFlow **never** auto-installs WSL, never runs `wsl --install`, never reboots your PC, and never enables Windows features on your behalf.

If WSL or Ubuntu is missing:

1. Follow [Microsoft’s official WSL install guide](https://learn.microsoft.com/windows/wsl/install).
2. Install the **Ubuntu** distribution.
3. Finish first launch: create a **Linux** username and password (this is not your Windows account).
4. Return to NeuroFlow when Ubuntu is ready.

**Admin rights** and a **possible reboot** are part of Microsoft’s installer — not NeuroFlow.

**Disk:** WSL does not ask you to reserve a fixed partition. The Ubuntu virtual disk (VHDX) **grows with use** (up to about 1 TB). NeuroFlow does not size or partition disks for you. FreeSurfer, FSL, and SCT will consume many gigabytes **inside Linux** once you install them.

## Where data lives

Jobs and datasets for packaged runs live under the **Ubuntu home directory**, typically `~/.neuroflow/` (see frozen defaults in the portal). They are **not** stored under `C:\Users\...` or on `/mnt/c` as the primary location.

Use the Ubuntu filesystem for NeuroFlow data and neuroimaging outputs.

## How to run (Windows release zip)

1. Download `neuroflow-*-windows-x86_64.zip` from [GitHub Releases](https://github.com/acsenrafilho/neuroflow/releases/latest).
2. Extract the archive. Keep **`NeuroFlow.exe`**, **`_internal/`**, and **`linux-payload/`** together — do not delete either folder.
3. Double-click **`NeuroFlow.exe`**.
4. If WSL or Ubuntu is missing, the launcher shows a short guide and links to Microsoft’s install page (still with **no** auto-install). Install Ubuntu yourself, then click again.
5. When Ubuntu is ready, the launcher copies the Linux portal into Ubuntu, starts it, and opens your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

The Windows process is a **thin launcher only**. FastAPI, allowlisted subprocesses, and host probes run **inside Ubuntu**. Module status reflects the **Ubuntu** PATH, not Windows.

**Zip contents:**

| Path | Role |
|------|------|
| `NeuroFlow.exe` | Windows WSL launcher |
| `_internal/` | PyInstaller runtime for the launcher (keep next to the exe) |
| `linux-payload/` | Same Linux portal onedir as the Linux release (`neuroflow` + `_internal/`) |
| `README-WINDOWS.txt` | One-page extract-and-run notes |

**SmartScreen:** unsigned builds may show “Windows protected your PC”. Choose **More info → Run anyway** when you trust the release source.

### Optional: Linux zip inside Ubuntu

Maintainers or advanced users can still extract the **Linux** release zip inside an Ubuntu terminal and run `./neuroflow/neuroflow`, then open Chrome on Windows at [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The supported end-user path is the Windows launcher zip above.

## Host tools in Ubuntu

NeuroFlow does **not** download or install FreeSurfer, FSL, or SCT. Install them with each vendor’s official procedure **inside Ubuntu**, ensure binaries are on the Ubuntu `PATH` (or set `NEUROFLOW_*` overrides), then open [Host tools](host-tools.md) in the app and click **Rescan host tools**. From a terminal you can also run:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/host/rescan
```

If Home shows **Install on host**, that means the probe did not find the CLI in **Ubuntu** — not a bug in the Windows PATH. After a successful rescan, reload Home so module badges refresh.

When FreeSurfer, FSL, and SCT are all missing, the Windows launcher may open the Host tools help page first so you see this path immediately.

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| Ubuntu not initialized | Open Ubuntu from the Start menu once and complete the Linux user setup. |
| Port 8000 busy | Stop the other process using port 8000, or wait until it finishes. NeuroFlow will not kill that process. |
| `linux-payload/` missing | Keep `linux-payload/` next to `NeuroFlow.exe` after extract, or set `NEUROFLOW_LINUX_PAYLOAD` to a Linux onedir (`neuroflow` + `_internal/`). |
| Second double-click | If the portal is already healthy, NeuroFlow only opens the browser again (no second server). |
| Browser cannot reach the portal on Windows 10 | WSL2 localhost forwarding differs on some Win10 setups; try accessing from inside Ubuntu first, or see Microsoft WSL networking docs. |
| ARM Windows | Not supported in v1; use an x86_64 Windows PC with WSL2. |
| Module stuck on Install on host | Install the package in **Ubuntu**, source its environment if needed, then rescan. |

Next: [Using the portal](using.md) · [Host tools](host-tools.md) · [FAQ](faq.md).

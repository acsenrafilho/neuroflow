# Host tools

NeuroFlow **detects** neuroimaging packages on the machine; it does **not** install them. Install FreeSurfer, FSL, and SCT with their official procedures, then ensure binaries are on `PATH` or set overrides in `.env`.

## Probes and overrides (portal packages)

| Package | Typical probe / override |
|---------|--------------------------|
| FreeSurfer | `recon-all` on `PATH`, or `NEUROFLOW_RECON_ALL_BIN` / `NEUROFLOW_FREESURFER_HOME` |
| FSL | `FSLDIR` / `NEUROFLOW_FSLDIR` |
| Spinal Cord Toolbox (SCT) | `sct_version` on `PATH`, `$HOME/sct_*` (official installer), or `SCT_DIR` / `NEUROFLOW_SCT_DIR` |

ANTs, 3D Slicer, and ITK have similar environment overrides in `.env.example` but are **not** shown in the portal UI yet.

## Scan and rescan

On API startup, NeuroFlow scans the host for registered packages and caches the result. After sourcing a tool environment, re-scan without restarting:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/host/rescan
```

From a terminal in the repo:

```bash
poetry run neuroflow
poetry run neuroflow scan
# or: ./scripts/check-host-tools.sh
```

`poetry run neuroflow` lists the data root and package readiness from the same probes used by the API.

## Windows / WSL

On Windows, the portal runs **inside WSL2 Ubuntu**. Host probes inspect the **Ubuntu** `PATH` and environment — not the native Windows PATH.

- Install FreeSurfer, FSL, SCT, and other packages **inside Ubuntu** with each vendor's official procedure.
- If Home shows **Install on host**, that is not a Windows-PATH bug; install or fix the tool in Ubuntu, then rescan.
- Jobs and datasets live under `~/.neuroflow/` in the Ubuntu home, not under `C:\Users\...` or `/mnt/c` as the primary store.

See [Windows and WSL](windows-wsl.md) for WSL setup (NeuroFlow never auto-installs WSL) and the supported run path.

## Reading module status

- **Ready** — binary found; you can open and run the module.
- **Install on host** — install or fix `PATH` / `.env`, then rescan.
- **Coming soon** — not available in the portal yet.

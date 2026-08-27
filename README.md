<p align="center">
  <img src="assets/images/neuroflow_logo.png" alt="NeuroFlow" width="360">
</p>

# NeuroFlow

**Neuroimaging CLI tools, one web page at a time.**

NeuroFlow is a **facilitation portal** for neuroscience medical image processing: **one independent page per CLI** (FreeSurfer, FSL, and Spinal Cord Toolbox in the portal today). Each module provides upload, parameter forms, command preview, and **local subprocess** execution.

It is **not** a multi-tool pipeline runner and **does not** ship Docker. The release is the **portal only** — it does **not** install FreeSurfer, FSL, or SCT, and there is **no login**. You install host packages yourself; NeuroFlow wraps them in a FastAPI + HTML/Tailwind UI.

[![CI](https://github.com/acsenrafilho/neuroflow/actions/workflows/ci.yml/badge.svg)](https://github.com/acsenrafilho/neuroflow/actions/workflows/ci.yml)
[![GitHub release](https://img.shields.io/github/v/release/acsenrafilho/neuroflow?sort=semver)](https://github.com/acsenrafilho/neuroflow/releases/latest)
[![Documentation Status](https://readthedocs.org/projects/neuroflowpipelines/badge/?version=latest)](https://neuroflowpipelines.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/acsenrafilho)](https://github.com/sponsors/acsenrafilho)

**Stack:** Python 3.10+ · Poetry · FastAPI · HTML/Tailwind · pytest · MkDocs

**Versioning:** [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`), starting at `0.0.1`. Merges to `main` drive releases via Conventional Commits (see [CHANGELOG.md](CHANGELOG.md)).

**Docs:** [User guide on Read the Docs](https://neuroflowpipelines.readthedocs.io/) · in-app help at `/help/` · OpenAPI at `/docs`

## Choose a path

- **[I only want to use NeuroFlow](#end-users--packaged-release)** — download a zip from GitHub Releases. No git, Poetry, or Node.
- **[I want to develop NeuroFlow](#developers--from-source)** — clone the repo on Ubuntu/Debian and run from source.

Full walkthroughs: [Installation](https://neuroflowpipelines.readthedocs.io/en/latest/user/installation/) · [Windows and WSL](https://neuroflowpipelines.readthedocs.io/en/latest/user/windows-wsl/) · [Development](https://neuroflowpipelines.readthedocs.io/en/latest/development/)

## End users — packaged release

Download the asset for your OS from the **[latest GitHub Release](https://github.com/acsenrafilho/neuroflow/releases/latest)**. Extract the archive and **keep the folder intact** (`_internal/` must stay next to the binary; on Windows also keep `linux-payload/`).

The app starts the local API, serves the UI, and opens [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Job and dataset files live under `~/.neuroflow/` in the environment where the portal runs (Ubuntu home on Windows via WSL — not under `C:\Users\...` as the primary store).

### Linux

1. Download `neuroflow-*-linux-*.zip` and extract it.
2. Make the binary executable: `chmod +x neuroflow/neuroflow`
3. Run: `./neuroflow/neuroflow`
4. A browser should open at [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Leave the terminal open while you use the portal.
5. Stop with **Ctrl+C** in that terminal.

Data: `~/.neuroflow/jobs` and `~/.neuroflow/datasets`.

### macOS (experimental)

1. Download `neuroflow-*-macos-*.zip` and extract it.
2. Run: `./neuroflow/neuroflow`
3. If Gatekeeper blocks the binary, use **System Settings → Privacy & Security → Open Anyway**, or after extract: `xattr -dr com.apple.quarantine neuroflow`
4. A browser should open at [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Leave the terminal open while you use the portal.
5. Stop with **Ctrl+C** in that terminal.

Install FreeSurfer, FSL, and SCT as **native macOS** packages where vendors support them.

### Windows

On Windows you click NeuroFlow, use the site in Chrome, and processing happens in Linux on WSL — if WSL and the neuroimaging tools are already installed. NeuroFlow points you to official docs; it does **not** install WSL or vendor CLIs.

**Requirements:** Windows 11 + WSL2 (primary; Windows 10 + WSL2 works with possible localhost caveats), distro name **Ubuntu**, **x86_64** only (ARM is refused).

1. Install **WSL2 + Ubuntu** yourself via [Microsoft’s WSL guide](https://learn.microsoft.com/windows/wsl/install). NeuroFlow never runs `wsl --install`, never reboots your PC, and never enables Windows features for you.
2. Open Ubuntu once and create a **Linux** username and password (not your Windows account).
3. Download `neuroflow-*-windows-x86_64.zip` and extract it. Keep **`NeuroFlow.exe`**, **`_internal/`**, and **`linux-payload/`** together.
4. Double-click **`NeuroFlow.exe`**.
5. If WSL or Ubuntu is missing, follow the on-screen Microsoft link, finish Ubuntu setup, then click again.
6. If SmartScreen warns (“Windows protected your PC”), choose **More info → Run anyway** when you trust the release source.
7. Stop the portal later with: `NeuroFlow.exe --stop` (does not shut down WSL; does not cancel running jobs).

Full path: [Windows and WSL on Read the Docs](https://neuroflowpipelines.readthedocs.io/en/latest/user/windows-wsl/).

### Then install host tools

The release zip does **not** include FreeSurfer, FSL, or SCT.

| Platform | Where to install tools |
|----------|------------------------|
| Linux / macOS | On that machine (`PATH` or `NEUROFLOW_*` env overrides) |
| Windows | **Inside WSL2 Ubuntu**, not on the native Windows PATH |

If Home shows **Install on host**, the probe failed on the OS where the portal runs (Ubuntu on Windows). Install the package, then rescan — see [Host tools](https://neuroflowpipelines.readthedocs.io/en/latest/user/host-tools/).

## Developers — from source

Development and from-source install target **Ubuntu 22.04+ / Debian 12+** with Poetry:

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
make setup
make api
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (with `NEUROFLOW_SERVE_FRONTEND=1` from `.env.example`).

Full from-source setup, desktop shortcut, frontend preview, and `make` targets: [Development](https://neuroflowpipelines.readthedocs.io/en/latest/development/) · [CONTRIBUTING.md](CONTRIBUTING.md).

## Project layout

```
neuroflow/          # Python package (api, tools, services)
frontend/           # Production UI (hub + per-tool pages)
packaging/          # Desktop entry + PyInstaller release build
doc/mockup/         # Legacy design reference mockups
doc/licenses/       # Third-party tool license notices
data/jobs/          # Job metadata and logs (gitignored contents)
data/datasets/      # BIDS-inspired workspace / subject trees
docs/               # MkDocs source
scripts/            # setup, launch, host scan helpers
tests/
```

## Docs and API

- User documentation: https://neuroflowpipelines.readthedocs.io/
- In-app user guide: http://127.0.0.1:8000/help/ (when the frontend is served)
- OpenAPI (Swagger): http://127.0.0.1:8000/docs
- Health: `GET /api/v1/health`

## Adding a tool

See [CONTRIBUTING.md](CONTRIBUTING.md). Short path:

1. Register the tool in `neuroflow/tools/registry.py`.
2. Add argv builder + launcher under `neuroflow/tools/<name>.py`.
3. Add API routes under `neuroflow/api/v1/tools.py` (or a dedicated router).
4. Add `frontend/src/pages/tools/<name>.html` following the FreeSurfer module pattern.

## Community

NeuroFlow is a personal project. Issues and pull requests are welcome; response time may vary.

- [Open an issue](https://github.com/acsenrafilho/neuroflow/issues/new/choose) for bugs, features, or questions (use the form that matches).
- Look for [`good first issue`](https://github.com/acsenrafilho/neuroflow/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) and [`help wanted`](https://github.com/acsenrafilho/neuroflow/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22).
- Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).
- Security reports: [SECURITY.md](SECURITY.md) (private advisory, not a public issue).

## Citation

If you use NeuroFlow in academic work, cite the software via [CITATION.cff](CITATION.cff) (GitHub **Cite this repository**).

## Sponsors

Optional [GitHub Sponsors](https://github.com/sponsors/acsenrafilho) support maintenance time. The software remains MIT-licensed either way.

## License

MIT — see [LICENSE](LICENSE). Third-party neuroimaging tools (FSL, ANTs, FreeSurfer, 3D Slicer) have separate licenses; see [doc/licenses/](doc/licenses/).

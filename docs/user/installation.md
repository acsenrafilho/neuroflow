# Installation

NeuroFlow is the portal (Python API + HTML UI). Neuroimaging CLIs such as FreeSurfer, FSL, and SCT stay on the **host** and are never installed by NeuroFlow. See [Host tools](host-tools.md).

## End users (packaged release)

The easiest path on **macOS** or **Linux** is a pre-built zip from GitHub Releases:

1. Open the [latest release](https://github.com/acsenrafilho/neuroflow/releases/latest).
2. Download the asset for your OS (`neuroflow-<version>-macos-*.zip` or `…-linux-…`).
3. Extract the archive and run the `neuroflow` executable inside the `neuroflow/` folder.
4. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) if the browser does not open automatically.

### Windows

On Windows, processing runs in **WSL2 Ubuntu** — not on native Windows. See **[Windows and WSL](windows-wsl.md)** for the full path.

1. Download `neuroflow-<version>-windows-x86_64.zip` from the [latest release](https://github.com/acsenrafilho/neuroflow/releases/latest).
2. Extract the archive. Keep `NeuroFlow.exe`, `_internal/`, and `linux-payload/` together.
3. Double-click **`NeuroFlow.exe`**. Install WSL2 + Ubuntu yourself first if needed ([Microsoft guide](https://learn.microsoft.com/windows/wsl/install)); NeuroFlow never auto-installs WSL.
4. Use Chrome (or your default browser) at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) while the portal runs inside Ubuntu.

Packaged builds store jobs and datasets under `~/.neuroflow/` in the environment where the portal runs (Ubuntu home when using WSL). They serve the UI by default and do **not** include FreeSurfer, FSL, or SCT — install those inside Ubuntu on Windows, or on the host on Linux/macOS. See [Host tools](host-tools.md).

**macOS Gatekeeper / Windows SmartScreen:** unsigned builds may need an explicit “Open anyway” / “Run anyway” confirmation.

## Developers (from source)

**OS:** Ubuntu 22.04+ or Debian 12+ with `apt` (other platforms: install the toolchain yourself; `make setup` is apt-only for now).

**Toolchain** (what `make setup` can check and suggest via apt / Poetry installer):

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- Node.js 18+ (frontend build)

### Install NeuroFlow from source

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
make setup
```

`make setup` runs `scripts/setup.sh`:

1. Verifies apt, Python, Poetry, and Node
2. Prints suggested `apt` / Poetry / NodeSource commands when something is missing
3. Asks before running those installs (`--yes` skips the prompt; `--dry-run` prints only)
4. Creates `.env` from `.env.example` if needed
5. Runs `poetry install`, builds the frontend, and runs an informational `neuroflow scan`

```bash
./scripts/setup.sh --dry-run   # print suggestions only
./scripts/setup.sh --yes       # apply suggested system installs without prompting
```

Manual path (when the toolchain is already installed):

```bash
cp .env.example .env
make install
make frontend-build
```

`.env.example` sets `NEUROFLOW_SERVE_FRONTEND=1` so the built UI is served from the API at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Run

### Development (terminal)

```bash
make api
# or: poetry run neuroflow serve
```

Uses uvicorn with auto-reload on `127.0.0.1:8000`.

### Desktop / application menu (Linux, from-source install)

After `make setup`:

```bash
make desktop-install
```

This installs a NeuroFlow entry under `~/.local/share/applications/` and, when present, `~/Desktop/`. Clicking it starts the API with `--no-reload` in the background and opens the browser.

Stop a background instance:

```bash
./scripts/neuroflow-stop.sh
```

### Local release zip (maintainers)

```bash
make release-build
```

Produces `dist/release/neuroflow-<version>-linux-<arch>.zip` via PyInstaller (requires the Poetry `packaging` group).

## URLs

On startup the API scans the local host for registered packages. The home **Processing modules** table lists **FreeSurfer**, **FSL**, and **SCT**.

| What | URL |
|------|-----|
| Tool hub | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| In-app user guide | [http://127.0.0.1:8000/help/](http://127.0.0.1:8000/help/) |
| FreeSurfer module | [http://127.0.0.1:8000/tools/freesurfer.html](http://127.0.0.1:8000/tools/freesurfer.html) |
| FSL package | [http://127.0.0.1:8000/packages/fsl.html](http://127.0.0.1:8000/packages/fsl.html) |
| SCT package | [http://127.0.0.1:8000/packages/sct.html](http://127.0.0.1:8000/packages/sct.html) |
| OpenAPI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |

After sourcing a tool environment (for example FreeSurfer), re-scan without restarting:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/host/rescan
```

## Frontend-only (separate port)

```bash
cd frontend/dist && python -m http.server 8080
```

Use the API on port 8000. Prefer serving the UI from the API (`NEUROFLOW_SERVE_FRONTEND=1`) so hub calls to `/api/v1/` share the same origin.

!!! warning "Do not serve `frontend/src/pages`"

    Always run `make frontend-build` and serve `frontend/dist/`. Opening source HTML directly breaks CSS and asset paths.

Next: [Using the portal](using.md).

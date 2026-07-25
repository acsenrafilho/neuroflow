# Getting started

NeuroFlow is the portal (Python API + HTML UI). Neuroimaging CLIs such as FreeSurfer and FSL stay on the **host** and are never installed by NeuroFlow.

## Prerequisites

**OS:** Ubuntu 22.04+ or Debian 12+ with `apt` (other platforms: install the toolchain yourself; `make setup` is apt-only for now).

**Toolchain** (what `make setup` can check and suggest via apt / Poetry installer):

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- Node.js 18+ (frontend build)

**Host neuroimaging tools (optional):** install separately on the machine if you need those modules. NeuroFlow only detects them. See [Host tools](#host-tools-optional) below.

## Install NeuroFlow

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

Flags:

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

`.env.example` sets `NEUROFLOW_SERVE_FRONTEND=1` so the built UI is served from the API at http://127.0.0.1:8000/.

## Run

### Development (terminal)

```bash
make api
# or: poetry run neuroflow serve
```

Uses uvicorn with auto-reload on `127.0.0.1:8000`.

### Desktop / application menu (Linux)

After `make setup`:

```bash
make desktop-install
```

This installs a NeuroFlow entry under `~/.local/share/applications/` and, when present, `~/Desktop/`. Clicking it starts the API with `--no-reload` in the background and opens the browser.

Stop a background instance:

```bash
./scripts/neuroflow-stop.sh
```

### URLs

On startup the API scans the local host for registered packages and caches the result. The home page **Processing modules** table currently lists **FreeSurfer** and **FSL** only (other packages remain in the codebase but are hidden from the portal).

- Tool hub: http://127.0.0.1:8000/
- In-app user guide: http://127.0.0.1:8000/help/
- FreeSurfer module: http://127.0.0.1:8000/tools/freesurfer.html
- FSL package: http://127.0.0.1:8000/packages/fsl.html
- FSL module (example): http://127.0.0.1:8000/tools/fsl.html?module=fsl-bet
- OpenAPI: http://127.0.0.1:8000/docs

After sourcing a tool environment (e.g. FreeSurfer), re-scan without restarting:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/host/rescan
```

## Host tools (optional)

NeuroFlow does **not** install FreeSurfer, FSL, ANTs, 3D Slicer, or ITK. Install them with their official procedures, then ensure binaries are on `PATH` or set overrides in `.env`:

| Package | Typical probe / override |
|---------|--------------------------|
| FreeSurfer | `recon-all` on `PATH`, or `NEUROFLOW_RECON_ALL_BIN` / `NEUROFLOW_FREESURFER_HOME` |
| FSL | `FSLDIR` / `NEUROFLOW_FSLDIR` |
| ANTs | `ANTSPATH` / `NEUROFLOW_ANTSPATH` |
| 3D Slicer | `SLICER_HOME` / `NEUROFLOW_SLICER_HOME` |
| ITK (CSIM) | paths in `config/itk-binaries.json` |

### CLI status and host scan

```bash
poetry run neuroflow
```

Lists the data root and package readiness from the same probes used by the API.

```bash
poetry run neuroflow scan
# or: ./scripts/check-host-tools.sh
```

FSL modules document prerequisite steps (e.g. TOPUP before EDDY, FDT before BEDPOSTX) on each tool page. Run each stage as a separate job; NeuroFlow does not chain pipelines automatically.

## Frontend-only (separate port)

```bash
cd frontend/dist && python -m http.server 8080
```

Use the API at port 8000; configure CORS origins in `neuroflow/api/main.py` if needed.

## Job data

- Job metadata and logs: `NEUROFLOW_DATA_ROOT` (default `./data/jobs`)
- Researcher datasets (BIDS-inspired): `NEUROFLOW_DATASETS_ROOT` (default `./data/datasets`)

Layout example:

```text
data/datasets/<workspace>/
  sub-001/anat/…
  derivatives/fsl/bet/…
  derivatives/freesurfer/sub-001/   # native FreeSurfer SUBJECTS_DIR tree
```

On each module page, set **Project / User name** (stored in the browser) and **Subject ID** (`sub-…`). The home page **Active processes** table lists running and queued jobs with a link back to the module. Finished jobs appear under **History** (`/history.html`). On API startup, orphaned `running`/`queued` jobs from a previous process are reconciled (failed or cancelled) so they do not clutter Active processes.

Host RAM/CPU limits (`NEUROFLOW_RAM_MAX_PERCENT`, `NEUROFLOW_CPU_MAX_PERCENT`) pause new starts into a queue when the machine is busy. Contents under `data/` are gitignored except `.gitkeep`.

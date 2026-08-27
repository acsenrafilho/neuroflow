# Development

Public user documentation is published at [https://neuroflowpipelines.readthedocs.io/](https://neuroflowpipelines.readthedocs.io/). Sources live under `docs/user/`.

This page is for people who **clone the repository** and run NeuroFlow from source. End users who only need the portal should use a [packaged release](user/installation.md) instead.

## Prerequisites

**OS:** Ubuntu 22.04+ or Debian 12+ with `apt` (`make setup` is apt-only for now).

**NeuroFlow toolchain:**

- Python 3.10+ (`>=3.10` in `pyproject.toml`)
- [Poetry](https://python-poetry.org/)
- [Node.js](https://nodejs.org/) 18+ (frontend Tailwind build)

**Host neuroimaging tools (optional)** — install on the machine yourself; NeuroFlow does not install them:

- **FreeSurfer** (`recon-all` on `PATH`, or `NEUROFLOW_RECON_ALL_BIN`)
- **FSL** (`bet`, `flirt`, etc. on `PATH`, or `NEUROFLOW_FSLDIR` / `FSLDIR`)
- **Spinal Cord Toolbox (SCT)** (`sct_version` on `PATH`, `$HOME/sct_*`, or `SCT_DIR` / `NEUROFLOW_SCT_DIR`)
- Optional (code present, hidden in the portal UI for now): ANTs, 3D Slicer, ITK

## First-machine setup

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
make setup
make api
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (with `NEUROFLOW_SERVE_FRONTEND=1` from `.env.example`). In-app user guide: [http://127.0.0.1:8000/help/](http://127.0.0.1:8000/help/). OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

`make setup` runs `scripts/setup.sh`: apt/Python/Poetry/Node checks, optional suggested installs, `.env` from `.env.example`, `poetry install`, frontend build, and an informational `neuroflow scan`.

```bash
./scripts/setup.sh --dry-run   # print suggestions only
./scripts/setup.sh --yes       # apply suggested system installs without prompting
```

### Manual install (toolchain already present)

```bash
cp .env.example .env
make install
make frontend-build
poetry run neuroflow serve
```

- `make setup` — first-machine bootstrap (apt checks, deps, frontend build)
- `make install` — Poetry + frontend npm when the toolchain is already present
- `make frontend-build` — Tailwind CSS and copy pages to `frontend/dist/`

## Run

```bash
make api
# or: poetry run neuroflow serve
# optional: --host 0.0.0.0 --port 8000 --no-reload
```

- `make api` / `neuroflow serve` — development defaults include **reload** on `127.0.0.1:8000`. Stop with **Ctrl+C**.
- Desktop launcher (`scripts/neuroflow-launch.sh`) uses **`--no-reload`** and may run in the background; stop with `./scripts/neuroflow-stop.sh`.

### Desktop / application menu (Linux)

After `make setup`:

```bash
make desktop-install
```

Then use the **NeuroFlow** icon (background server + browser). Stop with `./scripts/neuroflow-stop.sh`.

## Data roots (from source vs packaged)

| Mode | Jobs | Datasets |
|------|------|----------|
| From source (`.env.example`) | `./data/jobs` | `./data/datasets` |
| Packaged zip (frozen defaults) | `~/.neuroflow/jobs` | `~/.neuroflow/datasets` |

Override with `NEUROFLOW_DATA_ROOT` and `NEUROFLOW_DATASETS_ROOT`. See [Workspaces and data](user/workspaces.md).

## Viewing the frontend

The UI is **not** served from `frontend/src/pages/`. That folder is source only. Tailwind builds CSS and copies HTML into `frontend/dist/`, which is the deployable site.

**Always build before preview:**

```bash
make frontend-build
# or: cd frontend && npm run build
```

Pages link to absolute paths such as `/assets/app.css`. The web server root must therefore be `frontend/dist/`, not the repository root and not `src/pages/`.

| Method | URL | Notes |
|--------|-----|--------|
| FastAPI + static | http://127.0.0.1:8000/ | Set `NEUROFLOW_SERVE_FRONTEND=1` in `.env`. UI and API share the same origin. |
| Python | http://127.0.0.1:8080/ | `cd frontend/dist && python -m http.server 8080` |
| Live Server (VS Code / Cursor) | http://127.0.0.1:5500/ | Uses [`.vscode/settings.json`](https://github.com/acsenrafilho/neuroflow/blob/main/.vscode/settings.json) (`root`: `frontend/dist`). Install the **Live Server** extension, build the frontend, then **Go Live** from `frontend/dist/index.html` or the workspace. |

**Do not** open `http://127.0.0.1:5500/frontend/src/pages/index.html` — CSS and logo paths will 404 and the layout will look broken.

With Live Server on port 5500 and the API on port 8000, hub features that call `/api/v1/tools` require the API to be running; for a full stack preview, prefer `NEUROFLOW_SERVE_FRONTEND=1` on port 8000.

## Tooling

| Tool | Purpose |
|------|---------|
| Poetry | Python dependencies and virtualenv |
| pytest | Unit and API tests |
| ruff | Lint and format (also via pre-commit) |
| pre-commit | Git hooks; same checks as the CI lint job |
| debugpy | Debugger attach (VS Code / Cursor) |
| MkDocs Material | Documentation site |

## Commands

| Command | Description |
|---------|-------------|
| `make setup` | First-machine bootstrap (apt checks, deps, frontend build) |
| `make install` | Install Python and frontend dependencies |
| `make desktop-install` | Linux application menu + Desktop shortcut |
| `make test` | Run pytest |
| `make lint` | Run pre-commit hooks (ruff + file hygiene) |
| `make lint-fix` | Ruff autofix + format on `neuroflow` and `tests` |
| `make api` | Start FastAPI via `poetry run neuroflow serve` (reload; host package scan on startup) |
| `make stop` | Stop a background desktop instance |
| `make frontend-build` | Build Tailwind CSS and copy pages to `frontend/dist/` |
| `make release-build` | PyInstaller onedir zip under `dist/release/` |
| `make docs` | Serve MkDocs locally (user guide + developer pages) |

Local packaged zip (maintainers): `make release-build` → `dist/release/neuroflow-*-linux-*.zip`.

## Project packages

```
neuroflow/
  api/          # FastAPI routes
  tools/        # Per-tool argv builders and registry
  services/     # Job storage on disk
  models/       # Pydantic schemas
```

## Frontend vs mockups

- `frontend/` — built with Tailwind CLI; ship to `frontend/dist/`
- `doc/mockup/` — legacy static design references; not used by the build

## Pre-commit

Install hooks once after `poetry install`:

```bash
poetry run pre-commit install
```

CI and `make lint` run `pre-commit run --all-files` (Ruff plus trailing whitespace, YAML, large-file, and related checks). See [Contributing](contributing.md).

## Windows WSL launcher (maintainers)

Release zips already bundle `linux-payload/` next to `NeuroFlow.exe`. To dogfood from source with the same layout:

1. On Linux, build the portal onedir: `packaging/build_release.sh` → `dist/neuroflow/`.
2. On Windows (WSL2 Ubuntu ready), place that folder as `linux-payload/` next to the launcher, or set `NEUROFLOW_LINUX_PAYLOAD` to it.
3. Run: `poetry run python -m neuroflow.windows_launcher_app`

Or build the launcher onedir with `packaging/windows_launcher.spec` / `packaging/build_windows_launcher.ps1` and assemble with `packaging/assemble_windows_release.py`.

The launcher copies the onedir into Ubuntu at `~/.neuroflow-app/<version>/`, starts it with `NEUROFLOW_SKIP_BROWSER=1` and `NEUROFLOW_PORTAL_PIDFILE`, polls health from Windows, and opens the browser. Use `NeuroFlow.exe --stop` to terminate the portal (pidfile under `~/.neuroflow-app/`; never `wsl --shutdown`).

### Manual Windows QA checklist

CI has no real WSL and no FSL on `windows-latest`. Before a release, spot-check on a Win11 machine:

- [ ] WSL **absent**: guide + Microsoft URL; no feature enable / no `wsl --install`.
- [ ] Ubuntu **present**, tools **absent**: UI loads; modules show Install on host (or Host tools landing).
- [ ] Ubuntu + at least one CLI: Execute produces `run.log` as on Linux.
- [ ] Second double-click: only opens the browser.
- [ ] Two rapid double-clicks while starting: no second portal (`already starting` or browser only).
- [ ] `NeuroFlow.exe --stop` then health fails; running jobs are not killed by `--stop`.
- [ ] Port 8000 taken by a non-NeuroFlow process: clear error.
- [ ] ARM Windows (if available): calm refusal message; `--status` prints `arch=`.

## GitHub repository settings (maintainers)

Description, topics, social preview, Sponsors, labels, and branch protection are configured in the GitHub UI. The checklist is in [CONTRIBUTING.md](https://github.com/acsenrafilho/neuroflow/blob/main/CONTRIBUTING.md#maintainer-github-repository-settings).

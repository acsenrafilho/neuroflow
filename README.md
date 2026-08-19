# NeuroFlow

NeuroFlow is a **web portal** that wraps neuroimaging **CLI tools**—one independent page per software. Each module provides upload, parameter forms, command preview, and local execution via subprocess (no multi-tool pipelines, no Docker in this repo).

**Stack:** Python 3.10 · Poetry · FastAPI · HTML/Tailwind · pytest · MkDocs

## Prerequisites

**NeuroFlow toolchain** (Ubuntu 22.04+ / Debian 12+):

- [Poetry](https://python-poetry.org/) (Python 3.10+)
- [Node.js](https://nodejs.org/) 18+ (frontend Tailwind build)

On Debian/Ubuntu, `make setup` checks these and can suggest `apt` / Poetry installer commands.

**Host neuroimaging tools (optional)** — install on the machine yourself; NeuroFlow does not install them:

- **FreeSurfer** (`recon-all` on `PATH`, or `NEUROFLOW_RECON_ALL_BIN`)
- **FSL** (`bet`, `flirt`, etc. on `PATH`, or `NEUROFLOW_FSLDIR` / `FSLDIR`)
- **Spinal Cord Toolbox (SCT)** (`sct_version` on `PATH`, `$HOME/sct_*`, or `SCT_DIR` / `NEUROFLOW_SCT_DIR`)
- Optional (code present, hidden in the portal UI for now): ANTs, 3D Slicer, ITK

## Quick start (Ubuntu / Debian)

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
make setup
make api
```

Open http://127.0.0.1:8000/ (with `NEUROFLOW_SERVE_FRONTEND=1` from `.env.example`). In-app user guide: http://127.0.0.1:8000/help/. User documentation: https://neuroflowpipelines.readthedocs.io/. OpenAPI (Swagger): http://127.0.0.1:8000/docs.

For a one-click start from the application menu or Desktop:

```bash
make desktop-install
```

Then use the **NeuroFlow** icon (background server + browser). Stop with `./scripts/neuroflow-stop.sh`.

### Manual install (toolchain already present)

```bash
cp .env.example .env
make install
make frontend-build
poetry run neuroflow serve
```

Dev shortcuts: `poetry run neuroflow serve` (or `make api`) — uvicorn with reload on `127.0.0.1:8000`.

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
| Live Server (VS Code / Cursor) | http://127.0.0.1:5500/ | Uses [`.vscode/settings.json`](.vscode/settings.json) (`root`: `frontend/dist`). Install the **Live Server** extension, build the frontend, then **Go Live** from `frontend/dist/index.html` or the workspace. |

**Do not** open `http://127.0.0.1:5500/frontend/src/pages/index.html` — CSS and logo paths will 404 and the layout will look broken.

With Live Server on port 5500 and the API on port 8000, hub features that call `/api/v1/tools` require the API to be running; for a full stack preview, prefer `NEUROFLOW_SERVE_FRONTEND=1` on port 8000.

| Command | Description |
|---------|-------------|
| `make setup` | First-machine bootstrap (apt checks, deps, frontend build) |
| `make install` | Install Python and frontend dependencies |
| `make desktop-install` | Linux application menu + Desktop shortcut |
| `make test` | Run pytest |
| `make lint` | Run ruff check and format check |
| `make api` | Start FastAPI via `poetry run neuroflow serve` (reload; host package scan on startup) |
| `make frontend-build` | Build Tailwind CSS and copy pages to `frontend/dist/` |
| `make docs` | Serve MkDocs locally (user guide + developer pages) |

## Project layout

```
neuroflow/          # Python package (api, tools, services)
frontend/           # Production UI (hub + per-tool pages)
packaging/          # Desktop entry template (Linux)
doc/mockup/         # Legacy design reference mockups
doc/licenses/       # Third-party tool license notices
data/jobs/          # Job metadata and logs (gitignored contents)
data/datasets/      # BIDS-inspired workspace / subject trees
docs/               # MkDocs source
scripts/            # setup, launch, host scan helpers
tests/
```

## API

- User documentation: https://neuroflowpipelines.readthedocs.io/
- In-app user guide: http://127.0.0.1:8000/help/ (when frontend is served)
- OpenAPI: http://127.0.0.1:8000/docs
- Health: `GET /api/v1/health`
- Tools / modules: `GET /api/v1/tools`, `GET /api/v1/modules` (portal: FreeSurfer, FSL, SCT)
- Active jobs: `GET /api/v1/jobs`
- Host resources: `GET /api/v1/host/resources`
- FreeSurfer job: `POST /api/v1/tools/freesurfer/jobs` (multipart: files, `subject_ids`, `workspace`, …)
- FSL job: `POST /api/v1/tools/fsl/jobs` (multipart: files, `workspace`, `subject_id`, `module_id`, …)

## Adding a tool

1. Register the tool in `neuroflow/tools/registry.py`.
2. Add argv builder + launcher under `neuroflow/tools/<name>.py`.
3. Add API routes under `neuroflow/api/v1/tools.py` (or a dedicated router).
4. Add `frontend/src/pages/tools/<name>.html` following the FreeSurfer module pattern.

## License

MIT — see [LICENSE](LICENSE). Third-party neuroimaging tools (FSL, ANTs, FreeSurfer, 3D Slicer) have separate licenses; see [doc/licenses/](doc/licenses/).

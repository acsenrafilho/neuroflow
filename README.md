# NeuroFlow

NeuroFlow is a **web portal** that wraps neuroimaging **CLI tools**—one independent page per software. Each module provides upload, parameter forms, command preview, and local execution via subprocess (no multi-tool pipelines, no Docker in this repo).

**Stack:** Python 3.10 · Poetry · FastAPI · HTML/Tailwind · pytest · MkDocs

## Prerequisites

- [Poetry](https://python-poetry.org/) (Python 3.10+)
- [Node.js](https://nodejs.org/) 18+ (frontend Tailwind build)
- **FreeSurfer** on the host for the FreeSurfer module (`recon-all` on `PATH`, or set `NEUROFLOW_RECON_ALL_BIN`)
- **FSL** on the host for FSL modules (`bet`, `flirt`, etc. on `PATH`, or set `NEUROFLOW_FSLDIR` / `FSLDIR`)
- **ANTs** precompiled binaries on `PATH`, or set `NEUROFLOW_ANTSPATH` / `ANTSPATH` to the `bin` directory
- **3D Slicer** on the host for Slicer modules (`Slicer` on `PATH`, or set `NEUROFLOW_SLICER_HOME` / `SLICER_HOME`)
- **ITK (CSIM)** native filters: locally compiled binaries configured in `config/itk-binaries.json` (see `config/itk-binaries.example.json`); **Simple Filters** uses the same Slicer install as above

## Quick start

```bash
cp .env.example .env
# Optional: NEUROFLOW_SERVE_FRONTEND=1 to serve the built UI from FastAPI
poetry install
cd frontend && npm install && npm run build && cd ..
poetry run uvicorn neuroflow.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ (with `NEUROFLOW_SERVE_FRONTEND=1`) or http://127.0.0.1:8000/docs for the API.

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
| `make install` | Install Python and frontend dependencies |
| `make test` | Run pytest |
| `make lint` | Run ruff check and format check |
| `make api` | Start FastAPI with reload (host package scan on startup) |
| `make frontend-build` | Build Tailwind CSS and copy pages to `frontend/dist/` |
| `make docs` | Serve MkDocs locally |

## Project layout

```
neuroflow/          # Python package (api, tools, services)
frontend/           # Production UI (hub + per-tool pages)
doc/mockup/         # Legacy design reference mockups
doc/licenses/       # Third-party tool license notices
data/jobs/          # Job uploads and logs (gitignored contents)
docs/               # MkDocs source
tests/
```

## API

- OpenAPI: http://127.0.0.1:8000/docs
- Health: `GET /api/v1/health`
- Tools: `GET /api/v1/tools`
- FreeSurfer job: `POST /api/v1/tools/freesurfer/jobs` (multipart: file + form fields)
- FSL job: `POST /api/v1/tools/fsl/jobs` (multipart: files, `file_roles`, `module_id`, `parameters`)
- ANTs job: `POST /api/v1/tools/ants/jobs` (multipart: files, `file_roles`, `module_id`, `parameters`)
- 3D Slicer job: `POST /api/v1/tools/slicer/jobs` (multipart: files, `file_roles`, `module_id`, `parameters`)
- ITK job: `POST /api/v1/tools/itk/jobs` (multipart: files, `file_roles`, `module_id`, `parameters`; binary paths in `config/itk-binaries.json`)

## Adding a tool

1. Register the tool in `neuroflow/tools/registry.py`.
2. Add argv builder + launcher under `neuroflow/tools/<name>.py`.
3. Add API routes under `neuroflow/api/v1/tools.py` (or a dedicated router).
4. Add `frontend/src/pages/tools/<name>.html` following the FreeSurfer module pattern.

## License

MIT — see [LICENSE](LICENSE). Third-party neuroimaging tools (FSL, ANTs, FreeSurfer, 3D Slicer) have separate licenses; see [doc/licenses/](doc/licenses/).

# Getting started

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- Node.js 18+ (frontend build)
- FreeSurfer with `recon-all` available (for the FreeSurfer module)
- FSL with binaries on `PATH` or `FSLDIR` / `NEUROFLOW_FSLDIR` set (for FSL modules)

## Setup

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
cp .env.example .env
poetry install
cd frontend && npm install && npm run build && cd ..
```

Set `NEUROFLOW_SERVE_FRONTEND=1` in `.env` to serve the built UI from the API process.

## Run the API and UI

```bash
make api
# or: poetry run uvicorn neuroflow.api.main:app --reload --host 127.0.0.1 --port 8000
```

On startup the API scans the local host for registered packages (FreeSurfer, FSL, ANTs, 3D Slicer, ITK) and caches the result. The home page **Processing modules** table uses `GET /api/v1/modules` to show **Ready** when the corresponding software is installed, even for portal placeholders that are not yet executable from the UI.

- Tool hub: http://127.0.0.1:8000/
- FreeSurfer module: http://127.0.0.1:8000/tools/freesurfer.html
- FSL package: http://127.0.0.1:8000/packages/fsl.html
- FSL module (example): http://127.0.0.1:8000/tools/fsl.html?module=fsl-bet
- OpenAPI: http://127.0.0.1:8000/docs

After sourcing a tool environment (e.g. FreeSurfer), re-scan without restarting:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/host/rescan
```

## CLI status and host scan

```bash
poetry run neuroflow
```

Lists the data root and package readiness from the same probes used by the API.

```bash
poetry run neuroflow scan
# or: ./scripts/check-host-tools.sh
```

Prints package and module readiness for the current machine. Probes use `PATH`, optional `.env` overrides (`NEUROFLOW_RECON_ALL_BIN`, `NEUROFLOW_FREESURFER_HOME`, `NEUROFLOW_FSLDIR`), and common env vars such as `FSLDIR`.

FSL modules document prerequisite steps (e.g. TOPUP before EDDY, FDT before BEDPOSTX) on each tool page. Run each stage as a separate job; NeuroFlow does not chain pipelines automatically.

## Frontend-only (separate port)

```bash
cd frontend/dist && python -m http.server 8080
```

Use the API at port 8000; configure CORS origins in `neuroflow/api/main.py` if needed.

## Job data

Uploads and logs are stored under `NEUROFLOW_DATA_ROOT` (default `./data/jobs`). Contents are gitignored except `.gitkeep`.

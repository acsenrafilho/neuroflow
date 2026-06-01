# Getting started

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- Node.js 18+ (frontend build)
- FreeSurfer with `recon-all` available (for the FreeSurfer module)

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
poetry run uvicorn neuroflow.api.main:app --reload --host 127.0.0.1 --port 8000
```

- Tool hub: http://127.0.0.1:8000/
- FreeSurfer module: http://127.0.0.1:8000/tools/freesurfer.html
- OpenAPI: http://127.0.0.1:8000/docs

## CLI status

```bash
poetry run neuroflow
```

Lists the data root and whether each registered tool binary is on `PATH`.

## Frontend-only (separate port)

```bash
cd frontend/dist && python -m http.server 8080
```

Use the API at port 8000; configure CORS origins in `neuroflow/api/main.py` if needed.

## Job data

Uploads and logs are stored under `NEUROFLOW_DATA_ROOT` (default `./data/jobs`). Contents are gitignored except `.gitkeep`.

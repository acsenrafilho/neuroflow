# NeuroFlow

NeuroFlow is a **facilitation portal** for neuroscience medical image processing. It helps researchers work with **BIDS** datasets, run containerized pipelines (FSL, ANTs, and more), and browse results through a clear web UI.

**Stack:** Python 3.10 · Poetry · FastAPI · HTML/Tailwind · Docker · pytest · MkDocs

## Prerequisites

- [Poetry](https://python-poetry.org/) (Python 3.10)
- [Node.js](https://nodejs.org/) 18+ (frontend Tailwind build)
- [Docker](https://www.docker.com/) (processing modules)

## Quick start

```bash
# Backend
cp .env.example .env
poetry install
poetry run uvicorn neuroflow.api.main:app --reload --host 127.0.0.1 --port 8000

# Optional: sample BIDS dataset
./scripts/fetch_sample_bids.sh

# Frontend (independent from doc/mockup/)
cd frontend && npm install && npm run build
cd frontend/dist && python -m http.server 8080

# Or serve built frontend via API
# Set NEUROFLOW_SERVE_FRONTEND=1 in .env and rebuild frontend first
```

| Command | Description |
|---------|-------------|
| `make install` | Install Python and frontend dependencies |
| `make test` | Run pytest |
| `make lint` | Run ruff check and format check |
| `make api` | Start FastAPI with reload |
| `make frontend-build` | Build Tailwind CSS to `frontend/dist/` |
| `make docs` | Serve MkDocs locally |

## Project layout

```
neuroflow/          # Python package (api, bids, pipelines, services)
frontend/           # Production UI (Tailwind CLI build)
doc/mockup/         # Design reference mockups (CDN Tailwind)
docker/             # FSL, ANTs processing images
docs/               # MkDocs source (Read the Docs)
data/sample/        # Local BIDS data (gitignored contents)
tests/
```

## API

- OpenAPI: http://127.0.0.1:8000/docs
- Health: `GET /api/v1/health`
- Datasets: `GET /api/v1/datasets` (requires valid `NEUROFLOW_BIDS_ROOT`)

## Documentation

- Design system: [assets/DESIGN.md](assets/DESIGN.md)
- UI mockups (reference): [doc/mockup/](doc/mockup/)
- Developer docs: `make docs` or build on [Read the Docs](https://readthedocs.org/) using `.readthedocs.yaml`

## License

MIT — see [LICENSE](LICENSE). Third-party neuroimaging tools (FSL, ANTs) have separate licenses; see [doc/licenses/](doc/licenses/).

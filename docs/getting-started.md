# Getting started

## Requirements

- Python 3.10
- [Poetry](https://python-poetry.org/)
- Node.js 18+ (frontend build)
- Docker (processing modules)

## Setup

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
cp .env.example .env
poetry install
./scripts/fetch_sample_bids.sh
```

## Run the API

```bash
poetry run uvicorn neuroflow.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for interactive OpenAPI documentation.

## Run the frontend

```bash
cd frontend
npm install
npm run build
cd dist && python -m http.server 8080
```

The production UI lives in `frontend/`. Design reference mockups are in `doc/mockup/` and are **not** used by the build.

## Sample BIDS data

`./scripts/fetch_sample_bids.sh` creates a minimal dataset under `data/sample/`. Contents are gitignored except `.gitkeep`.

## Docker smoke test

```bash
docker compose build fsl
docker compose run --rm fsl
```

# Development

## Tooling

| Tool | Purpose |
|------|---------|
| Poetry | Python dependencies and virtualenv |
| pytest | Unit and API tests |
| ruff | Lint and format |
| debugpy | Debugger attach (VS Code / Cursor) |
| MkDocs Material | Documentation site |

## Commands

```bash
make install    # poetry + frontend npm
make test       # pytest
make lint       # ruff check + format check
make api        # poetry run neuroflow serve (uvicorn with reload)
make docs       # mkdocs serve
```

Local API shortcut:

```bash
poetry run neuroflow serve
# optional: --host 0.0.0.0 --port 8000 --no-reload
```

## Python version

The project requires **Python 3.10+** (`>=3.10` in `pyproject.toml`).

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

CI runs `ruff check` and `ruff format --check`. Run locally:

```bash
poetry run ruff check neuroflow tests
poetry run ruff format neuroflow tests
```

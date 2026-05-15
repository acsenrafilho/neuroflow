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
make api        # uvicorn with reload
make docs       # mkdocs serve
```

## Python version

The project pins **Python 3.10** (`>=3.10,<3.11` in `pyproject.toml`). Plan an upgrade to 3.11+ before deploying to environments where 3.10 is unavailable (3.10 EOL: October 2026).

## Project packages

```
neuroflow/
  api/          # FastAPI routes
  bids/         # pybids helpers
  pipelines/    # Docker orchestration (future)
  services/     # Business logic
  models/       # Pydantic schemas
```

## Frontend vs mockups

- `frontend/` — built with Tailwind CLI; ship to `frontend/dist/`
- `doc/mockup/` — static design references (CDN Tailwind); do not import into the build

## Pre-commit

CI runs `ruff check` and `ruff format --check`. Run locally:

```bash
poetry run ruff check neuroflow tests
poetry run ruff format neuroflow tests
```

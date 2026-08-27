# Development

Public user documentation is published at [https://neuroflowpipelines.readthedocs.io/](https://neuroflowpipelines.readthedocs.io/). Sources live under `docs/user/`.

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

```bash
make setup             # first-machine bootstrap (apt checks, deps, frontend build)
make install           # poetry + frontend npm (toolchain already present)
make desktop-install   # Linux application menu + Desktop shortcut
make test              # pytest
make lint              # pre-commit hooks (ruff + file hygiene)
make api               # poetry run neuroflow serve (uvicorn with reload)
make frontend-build    # Tailwind + copy pages to frontend/dist
make docs              # mkdocs serve
```

Local API shortcut:

```bash
poetry run neuroflow serve
# optional: --host 0.0.0.0 --port 8000 --no-reload
```

- `make api` / `neuroflow serve` — development defaults include **reload**.
- Desktop launcher (`scripts/neuroflow-launch.sh`) uses **`--no-reload`** and may run in the background; stop with `./scripts/neuroflow-stop.sh`.

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

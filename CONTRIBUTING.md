# Contributing to NeuroFlow

Thank you for helping improve NeuroFlow. This is a **personal** open-source
project with a single maintainer. Reviews and replies may take a few days.

Please use **English** for issues, pull requests, commit messages, code
comments, and documentation.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Where to start

- **Bug, feature, or question:** open an [issue](https://github.com/acsenrafilho/neuroflow/issues/new/choose) using the matching form. Do not put PHI, identifiable scans, or real subject IDs in screenshots or logs.
- **Documentation and first patches:** look for issues labeled `good first issue` or `help wanted`. Typical first contributions are copy fixes, a small HTML tweak on a tool page, or a pytest case that does not need FreeSurfer/FSL/SCT installed.
- **Security:** see [SECURITY.md](SECURITY.md) (private advisory, not a public issue).

User documentation: [https://neuroflowpipelines.readthedocs.io/](https://neuroflowpipelines.readthedocs.io/).

## Development setup

Prerequisites and first-machine bootstrap are in the [README](README.md). Short version on Ubuntu/Debian:

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
make setup
```

Install git hooks (same checks as CI):

```bash
poetry run pre-commit install
```

Useful commands:

| Command | Description |
|---------|-------------|
| `make lint` | Run all pre-commit hooks on the repo |
| `make lint-fix` | Ruff autofix + format on `neuroflow` and `tests` |
| `make test` | pytest |
| `make frontend-build` | Tailwind CSS and copy pages to `frontend/dist/` |
| `make api` | FastAPI with reload on `127.0.0.1:8000` |
| `make docs` | MkDocs live server |

Before you push, run:

```bash
make lint
make test
make frontend-build
```

## Code style

- **Python:** Ruff (see `[tool.ruff]` in `pyproject.toml`). Type hints on public APIs. Allowlisted subprocesses only; never `shell=True`.
- **Frontend:** Plain HTML + Tailwind. Follow `assets/DESIGN.md`. Do not edit `frontend/dist/` by hand.
- **Docs:** Update MkDocs under `docs/` and in-app help under `frontend/src/pages/help/` when user-visible behavior changes.

## Adding a neuroimaging tool

1. Register the tool in `neuroflow/tools/registry.py`.
2. Add argv builder and launcher under `neuroflow/tools/<name>.py`.
3. Add API routes under `neuroflow/api/v1/tools.py` (or a dedicated router).
4. Add `frontend/src/pages/tools/<name>.html` following an existing module page.
5. Add tests that do not require the host CLI unless you skip them when the binary is missing.

## Pull requests

- Open from a feature branch; fill in the PR template.
- Keep the change focused. Link the related issue.
- CI must pass (pre-commit, pytest on Python 3.10 and 3.12, frontend build, MkDocs).

## Issue labels

| Label | Use |
|-------|-----|
| `bug` | Something does not work as documented |
| `enhancement` | New behavior or a module |
| `question` | How-to or clarification (no Discussions yet) |
| `docs` | Documentation only |
| `good first issue` | Small, well-scoped, little project context |
| `help wanted` | Maintainer would like outside help |
| `ci` | GitHub Actions / hooks |
| `frontend` / `backend` | Area of the change |

## Maintainer: GitHub repository settings

These are not stored in git. After cloning a fresh GitHub project, set:

1. **Description:** `Web portal for neuroimaging CLIs: one page per tool (FreeSurfer, FSL, Spinal Cord Toolbox). FastAPI + HTML/Tailwind. Local subprocess, no Docker.`
2. **Website:** `https://neuroflowpipelines.readthedocs.io/`
3. **Topics:** `neuroimaging`, `neuroscience`, `freesurfer`, `fsl`, `spinal-cord-toolbox`, `fastapi`, `python`, `medical-imaging`, `bids`, `mri`, `open-source`
4. **Social preview:** 1280×640 image from `docs/assets/brand/`
5. **Features:** Issues on; Wikis off (docs are MkDocs)
6. **Sponsors:** enable [GitHub Sponsors](https://github.com/sponsors) on the `acsenrafilho` account (`.github/FUNDING.yml` is already in the repo)
7. **Labels:** create the labels in the table above if they are missing (`gh label create …` or the Issues UI)
8. **Branch protection** on `main`: require the CI workflow to pass and a maintaining review before merge

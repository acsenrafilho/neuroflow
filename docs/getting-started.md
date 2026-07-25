# Getting started

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- Node.js 18+ (frontend build)
- FreeSurfer with `recon-all` available (for the FreeSurfer module)
- FSL with binaries on `PATH` or `FSLDIR` / `NEUROFLOW_FSLDIR` set (for FSL modules)
- ANTs precompiled binaries on `PATH` or `NEUROFLOW_ANTSPATH` / `ANTSPATH` pointing at the install `bin` directory (for ANTs modules)

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
# or: poetry run neuroflow serve
```

On startup the API scans the local host for registered packages and caches the result. The home page **Processing modules** table currently lists **FreeSurfer** and **FSL** only (other packages remain in the codebase but are hidden from the portal).

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

Prints package and module readiness for the current machine. Probes use `PATH`, optional `.env` overrides (`NEUROFLOW_RECON_ALL_BIN`, `NEUROFLOW_FREESURFER_HOME`, `NEUROFLOW_FSLDIR`, `NEUROFLOW_ANTSPATH`), and common env vars such as `FSLDIR` and `ANTSPATH`.

FSL modules document prerequisite steps (e.g. TOPUP before EDDY, FDT before BEDPOSTX) on each tool page. Run each stage as a separate job; NeuroFlow does not chain pipelines automatically.

## Frontend-only (separate port)

```bash
cd frontend/dist && python -m http.server 8080
```

Use the API at port 8000; configure CORS origins in `neuroflow/api/main.py` if needed.

## Job data

- Job metadata and logs: `NEUROFLOW_DATA_ROOT` (default `./data/jobs`)
- Researcher datasets (BIDS-inspired): `NEUROFLOW_DATASETS_ROOT` (default `./data/datasets`)

Layout example:

```text
data/datasets/<workspace>/
  sub-001/anat/…
  derivatives/fsl/bet/…
  derivatives/freesurfer/sub-001/   # native FreeSurfer SUBJECTS_DIR tree
```

On each module page, set **Project / User name** (stored in the browser) and **Subject ID** (`sub-…`). The home page **Active processes** table lists running and queued jobs with a link back to the module.

Host RAM/CPU limits (`NEUROFLOW_RAM_MAX_PERCENT`, `NEUROFLOW_CPU_MAX_PERCENT`) pause new starts into a queue when the machine is busy. Contents under `data/` are gitignored except `.gitkeep`.

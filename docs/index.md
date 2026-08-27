![NeuroFlow](assets/brand/neuroflow_icon.png){ width="96" }

# NeuroFlow

**Neuroimaging tools, one page at a time.**

NeuroFlow is a **facilitation portal** for neuroscience medical image processing: **one web page per CLI tool** (FreeSurfer, FSL, and Spinal Cord Toolbox in the portal today).

## Features

- Tool hub and per-tool parameter forms
- Multipart upload and on-disk job folders
- Allowlisted subprocess execution with streamed logs
- FastAPI backend with OpenAPI contract
- Plain HTML + Tailwind frontend

## User guide

- [Getting started](getting-started.md) — which page to read (packaged vs develop)
- [Overview](user/overview.md) — purpose and objectives
- [Installation](user/installation.md) — packaged release and from-source setup
- [Windows and WSL](user/windows-wsl.md) — browser on Windows, compute in Ubuntu
- [Using the portal](user/using.md)
- [Tips](user/tips.md) and [FAQ](user/faq.md)

In the running app: [http://127.0.0.1:8000/help/](http://127.0.0.1:8000/help/)

This site: [https://neuroflowpipelines.readthedocs.io/](https://neuroflowpipelines.readthedocs.io/)

## Developers

- [Development](development.md)
- [Contributing](contributing.md)
- [Architecture](architecture.md)
- [API](api.md)
- [Security](security.md)

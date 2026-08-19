# FAQ

## What is NeuroFlow?

A local web portal that wraps neuroimaging CLIs: one page per module for upload, parameters, command preview, and logs. See [Overview](overview.md).

## Does NeuroFlow install FreeSurfer, FSL, or SCT?

No. Install those packages with their official installers. NeuroFlow only detects them. See [Host tools](host-tools.md).

## Why does a module say “Install on host”?

The probe binary was not found on `PATH` (and no matching `.env` override worked). Install the package, source its environment, then rescan or restart the API.

## Why is my job queued?

Host RAM or CPU is above `NEUROFLOW_RAM_MAX_PERCENT` / `NEUROFLOW_CPU_MAX_PERCENT`, or the queue is filling up toward `NEUROFLOW_MAX_QUEUED_JOBS`. Wait, stop other jobs, or free resources. See [Jobs, logs, and history](jobs.md).

## Where are outputs versus logs?

Logs and job metadata live under `NEUROFLOW_DATA_ROOT` (`./data/jobs` by default). Researcher-facing images and derivatives live under `NEUROFLOW_DATASETS_ROOT` (`./data/datasets`) in a per-subject tree. See [Workspaces and data](workspaces.md).

## Is there a login?

Not in the MVP. Anyone who can reach the API can start jobs. Do not expose it on the public internet. See [Data and privacy](privacy.md).

## Can I expose NeuroFlow on the internet?

Do not expose an unauthenticated instance. Restrict it to localhost or a trusted lab network.

## Does it run on Windows or macOS?

`make setup` is aimed at Ubuntu/Debian with `apt`. Other platforms need the toolchain (Python, Poetry, Node) installed manually. Host neuroimaging tools must still be native installs for that OS.

## Do I need Docker?

No. This repository does not require Docker. Tools must be installed on the host where the API runs.

## Is it multi-user?

There is no authentication or per-user isolation. Treat it as one trusted operator (or a small trusted lab) on a shared machine.

## Does it chain pipelines automatically?

No. Each module run is one job. Prerequisites (for example TOPUP before EDDY) are documented on the page; you run them separately.

## How do I stop the server?

Foreground `make api`: interrupt the terminal (Ctrl+C). Desktop/background: `./scripts/neuroflow-stop.sh`.

## What about ANTs, 3D Slicer, and ITK?

They are hidden from the portal (`visible_in_portal=False`). Use the enabled packages only until those appear as **Ready** on Home.

## How do I interpret vendor CLI errors?

Read `run.log` and the vendor **Official documentation** linked on the module page. NeuroFlow streams stdout/stderr; it does not replace package manuals.

## What file types can I upload?

Typical inputs are NIfTI (`.nii`, `.nii.gz`) and DICOM (`.dcm`), depending on the module. Check the form on each page.

## How large can uploads be?

Default maximum is 500 MB (`NEUROFLOW_MAX_UPLOAD_MB`). Increase it in `.env` if needed and if the disk can hold the data.

# Jobs, logs, and history

What happens after you press execute, and where to look when something fails.

## Status

Jobs move through states such as queued, running, succeeded, failed, or cancelled. The module page shows live status and log text. Home lists **Active processes** (running and queued) so you can jump back while another page is open.

Finished work appears under **History** (`/history.html`). On API startup, orphaned `running` or `queued` jobs from a previous process are reconciled (failed or cancelled) so they do not clutter Active processes.

You can stop a running job from the UI when the API exposes kill; that sets status to **cancelled**.

## Resource queue

Host RAM and CPU limits (`NEUROFLOW_RAM_MAX_PERCENT`, `NEUROFLOW_CPU_MAX_PERCENT`) can pause new starts into a queue when the machine is busy. `NEUROFLOW_MAX_QUEUED_JOBS` caps how many jobs may wait. Wait for capacity, or finish or stop existing jobs, then start again.

## On-disk layout

A typical FreeSurfer job folder looks like:

```text
data/jobs/freesurfer/{job_id}/
  input/       # uploaded NIfTI/DICOM
  output/      # SUBJECTS_DIR for recon-all
  meta.json    # status, parameters, command
  run.log      # merged stdout/stderr
```

Other tools follow the same pattern under `data/jobs/<tool>/`. Researcher-facing copies also appear under the [dataset tree](workspaces.md).

## Reading the log

The UI streams the same content written to `run.log`. Vendor CLIs print progress and errors there; use **Official documentation** for tool-specific messages.

## Host rescan

If you source FreeSurfer, FSL, or SCT after the API started, rescan:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/host/rescan
```

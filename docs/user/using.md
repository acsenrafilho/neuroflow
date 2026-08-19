# Using the portal

A practical path from the home page to a running (or queued) job. Examples use FreeSurfer, FSL, or SCT when those packages are **Ready** on the host.

## 1. Open Home and pick a module

From [http://127.0.0.1:8000/](http://127.0.0.1:8000/), use the **Processing modules** table or the sidebar package links (FreeSurfer, FSL, SCT). Open a module whose status is **Ready**. If you see **Install on host**, set up the CLI first—see [Host tools](host-tools.md).

## 2. Set workspace and subject

On the module page, enter a **Project / User name** (stored in the browser) and a **Subject ID** such as `sub-001`. These organize outputs under the datasets tree. Details: [Workspaces and data](workspaces.md).

## 3. Upload input data

Drag NIfTI or DICOM into the drop zone (or use the file picker). Files stay in a local job folder on the machine running NeuroFlow—they are not uploaded to a remote cloud service by the portal itself.

Default upload cap is `NEUROFLOW_MAX_UPLOAD_MB` (500 in `.env.example`).

## 4. Configure parameters

Form fields map to real CLI flags. Prefer the form over typing shell strings. Some FSL and SCT modules list prerequisite steps on the page—complete those as **separate jobs** when required.

## 5. Check the CLI preview

Review the command the portal will run. Arguments are built server-side from validated fields; only allowlisted executables may start.

## 6. Execute and monitor

Start the job and watch the log panel. Return to Home for **Active processes** (running and queued) with a link back to the module. Finished jobs appear under **History** (`/history.html`). If the host is busy, new jobs may wait in a queue—see [Jobs, logs, and history](jobs.md).

Use **NeuroFlow guide** on a module page for package notes, and **Official documentation** for vendor CLI details.

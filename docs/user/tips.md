# Tips

Short habits that keep jobs predictable.

- Prefer the **form and CLI preview**. Do not paste a full shell line into the portal; arguments are built server-side from validated fields.
- After `source` of FreeSurfer, FSL, or SCT, **rescan** the host (`POST /api/v1/host/rescan`) or restart the API so Home shows **Ready**.
- Run **one job per stage**. TOPUP before EDDY, FDT before BEDPOSTX, cord segmentation before `sct_process_segmentation`.
- Use a **stable workspace name** and coded subject IDs (`sub-001`), not real names in paths.
- Expect FreeSurfer `-all` to run for **hours**. Watch **Active processes** on Home, not only the module tab.
- If a job is **queued**, check RAM/CPU gates and `NEUROFLOW_MAX_QUEUED_JOBS`. Finish or stop other work, then retry.
- If the UI looks broken, run `make frontend-build` and serve `frontend/dist/` (or the API with `NEUROFLOW_SERVE_FRONTEND=1`). Do not open `frontend/src/pages` in the browser.
- Stop a desktop/background instance with `./scripts/neuroflow-stop.sh`.
- Large uploads: raise `NEUROFLOW_MAX_UPLOAD_MB` only if the host can store the data.
- Host-tool licenses are separate from NeuroFlow (MIT). See the [license notices](https://github.com/acsenrafilho/neuroflow/tree/main/doc/licenses) in the repository.
- Use **Official documentation** on each module page for vendor-specific errors and flags.

# Workspaces and data

How **Project / User name** and **Subject ID** organize data on disk.

## Project / User name

On each module page, the workspace name (often labeled Project / User name) is stored in the browser and used as the top-level folder under the datasets root. Prefer a stable lab or project label so outputs stay grouped across sessions.

On Home you can create a workspace folder, see which workspaces already exist (and how many subjects each has), set the current workspace for new jobs (**Use**), or open the folder in your system file manager (**Open folder**).

## Subject ID

Use a BIDS-style identifier such as `sub-001`. Avoid putting real names or clinical identifiers in paths when possible—see [Data and privacy](privacy.md).

## Where files live

Defaults (override with environment variables if needed):

- Job metadata and logs: `NEUROFLOW_DATA_ROOT` (default `./data/jobs`)
- Researcher datasets: `NEUROFLOW_DATASETS_ROOT` (default `./data/datasets`)

```text
data/datasets/<workspace>/
  sub-001/
    anat/…
    derivatives/
      fsl/bet/…
      freesurfer/          # native FreeSurfer tree (mri, surf, …)
      sct/<module>/…
```

Job runtime stays under `data/jobs/<tool>/<job_id>/`; that does not replace the dataset tree. Inputs and derivatives for a subject stay under that subject folder.

Legacy sibling folders at `<workspace>/derivatives/…` (without a subject) are obsolete for new jobs; they are not migrated automatically.

Contents under `data/` are gitignored except placeholders.

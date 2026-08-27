# Workspaces and data

How **Project / User name** and **Subject ID** organize data on disk.

## Project / User name

On each module page, the workspace name (often labeled Project / User name) is stored in the browser and used as the top-level folder under the datasets root. Prefer a stable lab or project label so outputs stay grouped across sessions.

On Home you can create a workspace folder, see which workspaces already exist (and how many subjects each has), set the current workspace for new jobs (**Use**), or open the folder in your system file manager (**Open folder**).

## Subject ID

Use a BIDS-style identifier such as `sub-001`. Avoid putting real names or clinical identifiers in paths when possible—see [Data and privacy](privacy.md).

## Where files live

Override with `NEUROFLOW_DATA_ROOT` and `NEUROFLOW_DATASETS_ROOT` if needed.

| Mode | Jobs (`NEUROFLOW_DATA_ROOT`) | Datasets (`NEUROFLOW_DATASETS_ROOT`) |
|------|------------------------------|--------------------------------------|
| From source | `./data/jobs` | `./data/datasets` |
| Packaged zip (frozen defaults) | `~/.neuroflow/jobs` | `~/.neuroflow/datasets` |

On Windows, the packaged portal runs inside WSL2 Ubuntu, so `~/.neuroflow/` is the **Ubuntu** home — not under `C:\Users\...` as the primary store. See [Windows and WSL](windows-wsl.md).

Layout under the datasets root (paths relative to that root):

```text
<datasets_root>/<workspace>/
  sub-001/
    anat/…
    derivatives/
      fsl/bet/…
      freesurfer/          # native FreeSurfer tree (mri, surf, …)
      sct/<module>/…
```

Job runtime stays under `<data_root>/<tool>/<job_id>/`; that does not replace the dataset tree. Inputs and derivatives for a subject stay under that subject folder.

Legacy sibling folders at `<workspace>/derivatives/…` (without a subject) are obsolete for new jobs; they are not migrated automatically.

Contents under `./data/` in a git checkout are gitignored except placeholders.

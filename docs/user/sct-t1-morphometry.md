# T1 cervical morphometry (SCT)

Use this checklist when you have **T1-weighted brain (head) images** and need spinal cord **cross-sectional area (CSA)** and shape metrics at **C1, C2, and C3**. NeuroFlow runs **one SCT command per job**. It does not chain stages.

Typical T1 of the head includes the upper cervical cord in the inferior field of view. If C1–C3 are cropped, exclude the scan.

Gray-matter area (T2\*) and diffusion (DTI) are **not** part of this workflow.

## Job order

| Step | Module | Key settings | Pass / fail |
|------|--------|----------------|-------------|
| 0 | Visual check | C1–C3 in the FOV | Exclude if the cord is cropped |
| 1 | [sct_deepseg](/tools/sct.html?module=sct-deepseg) | task `spinalcord` | Mask is continuous; little or no CSF leak at the foramen magnum |
| 2 | [sct_qc](/tools/sct.html?module=sct-qc) | `-p sct_deepseg_sc`, T1 + segmentation | Open `index.html` on disk; overlay looks acceptable |
| 3 | [sct_label_vertebrae](/tools/sct.html?module=sct-label-vertebrae) | contrast **t1**, T1 + segmentation | C1, C2, and C3 match anatomy |
| 4 | [sct_qc](/tools/sct.html?module=sct-qc) | `-p sct_label_vertebrae`, T1 + labeled segmentation | Labels are not shifted |
| 5 | [sct_process_segmentation](/tools/sct.html?module=sct-process-segmentation) | segmentation + vertfile, `-vert 1:3`, `-perlevel 1` | CSV has one row per level 1–3 |

The portal default contrast for labeling is **t2**. For this T1 workflow, set **t1**.

`sct_qc` writes an HTML report with PNG overlays. NeuroFlow does not embed an image viewer: open `index.html` under `sub-<id>/derivatives/sct/qc/` (or the job output folder).

If automatic labeling fails at the cranio-cervical junction, correct labels on the host (FSLeyes or `sct_label_utils`) and re-run step 5. Those correction tools are not modules in the portal.

## CSV columns

Keep these columns for analysis (do not use a global CSA CSV without `-vert`):

- Vertebral level
- `MEAN(area)` — CSA (mm²)
- `MEAN(diameter_AP)` — anteroposterior diameter (flattening)
- `MEAN(diameter_RL)` — right–left diameter (optional ratio AP/RL)
- `MEAN(eccentricity)`

`-vert` and `-perlevel` require a vertebral label file (`vertfile`). Angle correction (`-angle-corr`) defaults to on.

## Batch

Process **one subject at a time** until QC is stable (about 3–5 cases). Then you can upload multiple T1s on the primary input of the same module; the portal still runs **one CLI per file**, sequentially.

PAM50 registration (`sct_register_to_template`) is not required for native-space CSA at C1–C3.

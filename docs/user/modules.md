# Packages and modules

The portal currently lists **FreeSurfer**, **FSL**, and **Spinal Cord Toolbox (SCT)**. For CLI flag reference, always open **Official documentation** on the module page. NeuroFlow is a facilitator, not a complete vendor manual.

Run each stage as a **separate job**. The portal does not chain pipelines automatically.

## FreeSurfer

Cortical reconstruction and volumetric segmentation (`recon-all`).

| Module | What it does | Typical duration (order of magnitude) |
|--------|----------------|----------------------------------------|
| recon-all (`-all`) | Full cortical reconstruction from T1-weighted MRI | Hours (often ~8 h per scan) |
| autorecon1 | Motion correction and intensity normalization | ~1 h |
| autorecon2 | Subcortical segmentation | ~2 h |
| autorecon3 | Cortical surface reconstruction | ~3 h |

- Package page: [http://127.0.0.1:8000/packages/freesurfer.html](http://127.0.0.1:8000/packages/freesurfer.html)
- Module page: [http://127.0.0.1:8000/tools/freesurfer.html](http://127.0.0.1:8000/tools/freesurfer.html)
- Vendor: [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/)

Outputs go under `sub-<id>/derivatives/freesurfer/` (recon-all `-s freesurfer`).

## FSL

Structural, diffusion, and registration tools. One module page per program (`/tools/fsl.html?module=…`).

| Module | CLI (typical) | Notes |
|--------|----------------|-------|
| BET | `bet` / `bet2` | Skull-stripping |
| FAST | `fast` | Tissue-class segmentation |
| FIRST | `run_first_all` | Subcortical structures |
| BIANCA | `bianca` | WMH classification (feature-file based) |
| SIENA | `siena` | Two time-point T1 change |
| TOPUP | `topup` | Distortion correction from opposing PE |
| EDDY | `eddy` | Eddy-current and movement correction; often needs TOPUP first |
| FDT (dtifit) | `dtifit` | DTI parameter maps |
| BEDPOSTX | `bedpostx` | Multi-fibre model; often after FDT |
| TBSS | `tbss_1_preproc` | Step 1 only in the portal |
| FLIRT | `flirt` | Linear registration |
| FNIRT | `fnirt` | Non-linear; typically needs a FLIRT affine |
| SUSAN | `susan` | Noise reduction |
| epi_reg | `epi_reg` | EPI to structural |
| MCFLIRT | `mcflirt` | Motion correction for time series |

Many advanced modules show a **Before you run** panel. Complete those steps as other jobs or with prepared inputs.

- Package: [http://127.0.0.1:8000/packages/fsl.html](http://127.0.0.1:8000/packages/fsl.html)
- Example: [http://127.0.0.1:8000/tools/fsl.html?module=fsl-bet](http://127.0.0.1:8000/tools/fsl.html?module=fsl-bet)
- Vendor: [FSL documentation](https://fsl.fmrib.ox.ac.uk/fsl/docs/index.html)

Outputs land under `sub-<id>/derivatives/fsl/<module>/`.

## Spinal Cord Toolbox (SCT)

Spinal cord MRI segmentation, vertebral labeling, PAM50 template registration, and morphometrics.

| Module | CLI | Notes |
|--------|-----|-------|
| sct_deepseg | `sct_deepseg` | Deep-learning segmentation (task-based) |
| sct_propseg | `sct_propseg` | Propagation-based segmentation |
| sct_get_centerline | `sct_get_centerline` | Centerline extraction |
| sct_create_mask | `sct_create_mask` | Cylindrical or box mask |
| sct_label_vertebrae | `sct_label_vertebrae` | Vertebral levels |
| sct_register_to_template | `sct_register_to_template` | Register anatomy to PAM50 |
| sct_warp_template | `sct_warp_template` | Warp template/atlases |
| sct_apply_transfo | `sct_apply_transfo` | Apply warps or affines |
| sct_process_segmentation | `sct_process_segmentation` | CSA and morphometrics from a segmentation |

Typical order for morphometrics: segment the cord, then process the segmentation. Registration and warps are separate jobs.

- Package: [http://127.0.0.1:8000/packages/sct.html](http://127.0.0.1:8000/packages/sct.html)
- Example: [http://127.0.0.1:8000/tools/sct.html?module=sct-deepseg](http://127.0.0.1:8000/tools/sct.html?module=sct-deepseg)
- Vendor: [Spinal Cord Toolbox](https://spinalcordtoolbox.com/stable/)

Outputs land under `sub-<id>/derivatives/sct/<module>/`.

## Coming later (not in the portal UI)

ANTs, 3D Slicer, and ITK may exist in the codebase. They are **not** listed as interactive packages on Home. Do not expect those pages in the sidebar until they are enabled and **Ready**.

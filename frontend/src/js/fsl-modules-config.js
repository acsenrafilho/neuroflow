/**
 * FSL module metadata: prerequisites, inputs, parameters, and CLI preview hints.
 * @type {Record<string, object>}
 */
const FSL_MODULES = {
  "fsl-bet": {
    moduleName: "BET",
    batchDriverRole: "input",
    summary:
      "Brain Extraction Tool — skull-strip structural MRI. Choose standard BET or BET2.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BET",
    docsLabel: "FSL BET user guide",
    estimatedHours: 0.05,
    prerequisites: [],
    inputs: [
      {
        role: "input",
        label: "Structural image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "bet_mode",
        label: "Extraction mode",
        type: "select",
        default: "bet",
        options: [
          { value: "bet", label: "Standard BET" },
          { value: "bet2", label: "BET2 (when installed)" },
        ],
      },
      {
        name: "fractional_intensity",
        label: "Fractional intensity threshold (-f)",
        type: "number",
        default: 0.5,
        step: 0.05,
        min: 0,
        max: 1,
      },
      {
        name: "vertical_gradient",
        label: "Vertical gradient (-g)",
        type: "number",
        default: 0,
        step: 0.1,
      },
      {
        name: "generate_mask",
        label: "Output binary brain mask (-m)",
        type: "checkbox",
        default: false,
      },
      {
        name: "robust",
        label: "Robust centre estimation (-R)",
        type: "checkbox",
        default: false,
      },
      {
        name: "remove_neck",
        label: "Remove neck (-n)",
        type: "checkbox",
        default: false,
      },
    ],
  },
  "fsl-fast": {
    moduleName: "FAST",
    batchDriverRole: "input",
    summary: "Tissue-type segmentation of structural images.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST",
    docsLabel: "FSL FAST user guide",
    estimatedHours: 0.25,
    prerequisites: [
      {
        text: "Run BET on your T1-weighted image to skull-strip before FAST (recommended).",
        moduleId: "fsl-bet",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "T1-weighted image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "tissue_type",
        label: "Tissue type (-t)",
        type: "number",
        default: 1,
        min: 1,
        max: 3,
      },
      {
        name: "n_segments",
        label: "Number of tissue classes (-n)",
        type: "number",
        default: 3,
        min: 1,
        max: 4,
      },
    ],
  },
  "fsl-susan": {
    moduleName: "SUSAN",
    batchDriverRole: "input",
    summary: "Noise reduction using SUSAN smoothing.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/SUSAN",
    docsLabel: "FSL SUSAN user guide",
    estimatedHours: 0.1,
    prerequisites: [
      {
        text: "Optional: skull-strip with BET first for structural images.",
        moduleId: "fsl-bet",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "Input image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "effective_sigma",
        label: "Effective sigma",
        type: "number",
        default: 3.0,
        step: 0.5,
      },
      {
        name: "mixture_value",
        label: "Mixture value",
        type: "number",
        default: 0.0,
        step: 0.1,
      },
    ],
  },
  "fsl-mcflirt": {
    moduleName: "MCFLIRT",
    batchDriverRole: "input",
    summary: "Motion correction for 4D fMRI or diffusion time series.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/MCFLIRT",
    docsLabel: "FSL MCFLIRT user guide",
    estimatedHours: 0.25,
    prerequisites: [
      {
        text: "Optional: provide a brain mask from BET for improved registration.",
        moduleId: "fsl-bet",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "4D time series (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "motion_model",
        label: "Motion model (-m)",
        type: "select",
        default: "2",
        options: [
          { value: "0", label: "0 — none" },
          { value: "1", label: "1 — translation" },
          { value: "2", label: "2 — rigid body (default)" },
        ],
      },
      {
        name: "cost",
        label: "Cost function (-cost)",
        type: "text",
        default: "mutualinfo",
      },
      {
        name: "generate_plots",
        label: "Generate motion plots (-plots)",
        type: "checkbox",
        default: true,
      },
    ],
  },
  "fsl-flirt": {
    moduleName: "FLIRT",
    batchDriverRole: null,
    summary: "Affine linear registration between two images.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT",
    docsLabel: "FSL FLIRT user guide",
    estimatedHours: 0.1,
    prerequisites: [
      {
        text: "Optional: skull-strip moving and reference images with BET.",
        moduleId: "fsl-bet",
      },
    ],
    inputs: [
      {
        role: "moving",
        label: "Moving image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "reference",
        label: "Reference image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "mask",
        label: "Reference weight mask (optional)",
        required: false,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
    ],
    params: [
      {
        name: "dof",
        label: "Degrees of freedom (-dof)",
        type: "number",
        default: 6,
        min: 3,
        max: 12,
      },
      {
        name: "cost",
        label: "Cost function (-cost)",
        type: "text",
        default: "corratio",
      },
      {
        name: "save_matrix",
        label: "Save affine matrix (-omat)",
        type: "checkbox",
        default: true,
      },
    ],
  },
  "fsl-fnirt": {
    moduleName: "FNIRT",
    batchDriverRole: "moving",
    summary: "Non-linear registration; requires a FLIRT affine transform.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FNIRT",
    docsLabel: "FSL FNIRT user guide",
    estimatedHours: 0.5,
    prerequisites: [
      {
        text: "Run FLIRT first and upload the affine matrix (.mat) produced with -omat.",
        moduleId: "fsl-flirt",
      },
    ],
    inputs: [
      {
        role: "moving",
        label: "Moving image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "reference",
        label: "Reference image (NIfTI, shared)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
      {
        role: "affine_mat",
        label: "FLIRT affine matrix (.mat, shared)",
        required: true,
        accept: ".mat",
        multiple: false,
      },
    ],
    params: [],
  },
  "fsl-first": {
    moduleName: "FIRST",
    batchDriverRole: "input",
    summary: "Subcortical structure segmentation (run_first_all).",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST",
    docsLabel: "FSL FIRST user guide",
    estimatedHours: 1.0,
    prerequisites: [
      {
        text: "Run BET on the T1-weighted image before FIRST (recommended).",
        moduleId: "fsl-bet",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "T1-weighted image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [],
  },
  "fsl-epi-reg": {
    moduleName: "epi_reg",
    batchDriverRole: "epi",
    summary: "Register EPI to structural (T1) space.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FEAT",
    docsLabel: "FSL registration guides",
    estimatedHours: 0.25,
    prerequisites: [
      {
        text: "Skull-strip the T1 with BET to produce the T1 brain image.",
        moduleId: "fsl-bet",
      },
    ],
    inputs: [
      {
        role: "epi",
        label: "EPI image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "t1",
        label: "T1 image (NIfTI, shared)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
      {
        role: "t1_brain",
        label: "T1 brain (BET output, shared)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
    ],
    params: [
      {
        name: "dof",
        label: "Degrees of freedom (--dof)",
        type: "number",
        default: 6,
        min: 3,
        max: 12,
      },
    ],
  },
  "fsl-siena": {
    moduleName: "SIENA",
    batchDriverRole: null,
    summary: "Longitudinal atrophy analysis between two brain-extracted T1 scans.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/SIENA",
    docsLabel: "FSL SIENA user guide",
    estimatedHours: 0.5,
    prerequisites: [
      {
        text: "Run BET on both time-point T1 images before SIENA.",
        moduleId: "fsl-bet",
      },
    ],
    inputs: [
      {
        role: "time1",
        label: "Time 1 brain image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "time2",
        label: "Time 2 brain image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [],
  },
  "fsl-topup": {
    moduleName: "TOPUP",
    batchDriverRole: "input",
    summary: "Correct susceptibility distortions using opposing phase-encode DWI.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TOPUP",
    docsLabel: "FSL TOPUP user guide",
    estimatedHours: 0.5,
    prerequisites: [
      {
        text: "Prepare a 4D NIfTI with blip-up and blip-down volumes and an acqparams file.",
        moduleId: null,
      },
    ],
    inputs: [
      {
        role: "input",
        label: "4D DWI (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "acqp",
        label: "Acquisition parameters (acqparams.txt, shared)",
        required: true,
        accept: ".txt",
        multiple: false,
      },
    ],
    params: [
      {
        name: "readout",
        label: "Total readout time (--readout)",
        type: "number",
        default: "",
        step: 0.01,
      },
    ],
  },
  "fsl-eddy": {
    moduleName: "EDDY",
    batchDriverRole: "input",
    summary: "Eddy-current and head-motion correction for diffusion MRI.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/EDDY",
    docsLabel: "FSL EDDY user guide",
    estimatedHours: 1.0,
    prerequisites: [
      {
        text: "Run TOPUP on your data (recommended) before EDDY.",
        moduleId: "fsl-topup",
      },
      {
        text: "Prepare index, acqp, bvals, and bvecs files matching your acquisition.",
        moduleId: null,
      },
    ],
    inputs: [
      {
        role: "input",
        label: "4D DWI (TOPUP-corrected or raw, NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "mask",
        label: "Brain mask (NIfTI, shared)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
      {
        role: "index",
        label: "Index file (index.txt, shared)",
        required: true,
        accept: ".txt",
        multiple: false,
      },
      {
        role: "acqp",
        label: "Acquisition parameters (acqparams.txt, shared)",
        required: true,
        accept: ".txt",
        multiple: false,
      },
      {
        role: "bvecs",
        label: "b-vectors file (shared)",
        required: true,
        accept: ".txt",
        multiple: false,
      },
      {
        role: "bvals",
        label: "b-values file (shared)",
        required: true,
        accept: ".txt,.bval",
        multiple: false,
      },
    ],
    params: [
      {
        name: "n_threads",
        label: "OpenMP threads (--nthr)",
        type: "number",
        default: 4,
        min: 1,
        max: 32,
      },
    ],
  },
  "fsl-fdt": {
    moduleName: "FDT (dtifit)",
    batchDriverRole: "input",
    summary: "Fit diffusion tensors and produce FA/MD maps (dtifit).",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT",
    docsLabel: "FSL FDT user guide",
    estimatedHours: 0.25,
    prerequisites: [
      {
        text: "Run EDDY (after TOPUP) on your diffusion data first.",
        moduleId: "fsl-eddy",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "Eddy-corrected 4D DWI (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "bvecs",
        label: "b-vectors file (shared)",
        required: true,
        accept: ".txt",
        multiple: false,
      },
      {
        role: "bvals",
        label: "b-values file (shared)",
        required: true,
        accept: ".txt,.bval",
        multiple: false,
      },
      {
        role: "mask",
        label: "Brain mask (optional, shared)",
        required: false,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
    ],
    params: [],
  },
  "fsl-bedpostx": {
    moduleName: "BEDPOSTX",
    batchDriverRole: "subject_dir",
    summary: "Multi-fibre diffusion modelling on a prepared subject directory.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Fdt+Utilities+and+GUI",
    docsLabel: "FSL FDT / bedpostX guide",
    estimatedHours: 4.0,
    prerequisites: [
      {
        text: "Run FDT (dtifit) on eddy-corrected data and assemble the subject folder.",
        moduleId: "fsl-fdt",
      },
      {
        text:
          "Upload a zip of the subject directory containing nodif_brain_mask, data.nii.gz, bvecs, and bvals.",
        moduleId: null,
      },
    ],
    inputs: [
      {
        role: "subject_dir",
        label: "Subject directory (.zip, one per run)",
        required: true,
        accept: ".zip",
        multiple: true,
      },
    ],
    params: [
      {
        name: "n_fibres",
        label: "Number of fibres per voxel",
        type: "number",
        default: 2,
        min: 1,
        max: 3,
      },
    ],
  },
  "fsl-tbss": {
    moduleName: "TBSS",
    batchDriverRole: "fa",
    summary: "TBSS step 1 — pre-process a single FA map (tbss_1_preproc).",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TBSS",
    docsLabel: "FSL TBSS user guide",
    estimatedHours: 0.1,
    prerequisites: [
      {
        text: "Generate FA maps with FDT (dtifit) for each subject first.",
        moduleId: "fsl-fdt",
      },
      {
        text:
          "After pre-processing all subjects, run tbss_2, tbss_3, and tbss_4 manually on the host (not chained here).",
        moduleId: null,
      },
    ],
    inputs: [
      {
        role: "fa",
        label: "FA map(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [],
  },
  "fsl-bianca": {
    moduleName: "BIANCA",
    batchDriverRole: "feature_file",
    summary: "White-matter hyperintensity classification using a feature file.",
    docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BIANCA",
    docsLabel: "FSL BIANCA user guide",
    estimatedHours: 0.5,
    prerequisites: [
      {
        text: "Build feature files following the BIANCA training workflow (often uses FLIRT outputs).",
        moduleId: "fsl-flirt",
      },
      {
        text: "Train and validate models on the host before applying to new subjects.",
        moduleId: null,
      },
    ],
    inputs: [
      {
        role: "feature_file",
        label: "BIANCA feature file(s)",
        required: true,
        accept: ".txt",
        multiple: true,
      },
    ],
    params: [],
  },
};

if (typeof window !== "undefined") {
  window.FSL_MODULES = FSL_MODULES;
}

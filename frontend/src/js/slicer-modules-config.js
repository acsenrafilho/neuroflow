/**
 * 3D Slicer module metadata: prerequisites, inputs, parameters, and CLI preview hints.
 * @type {Record<string, object>}
 */
const SLICER_MODULES = {
  "slicer-dwi-convert": {
    moduleName: "DWIConvert",
    batchDriverRole: "input",
    launchName: "DWIConvert",
    summary:
      "Convert FSL-format DWI (NIfTI + bvals/bvecs) to NRRD for downstream Slicer diffusion modules.",
    docsUrl: "https://slicer.readthedocs.io/en/latest/",
    docsLabel: "3D Slicer documentation",
    estimatedHours: 0.1,
    prerequisites: [],
    inputs: [
      {
        role: "input",
        label: "4D DWI (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "bvals",
        label: "b-values file (shared)",
        required: true,
        accept: ".txt,.bval",
        multiple: false,
      },
      {
        role: "bvecs",
        label: "b-vectors file (shared)",
        required: true,
        accept: ".txt,.bvec",
        multiple: false,
      },
    ],
    params: [
      {
        name: "conversion_mode",
        label: "Conversion mode (--conversionMode)",
        type: "select",
        default: "FSLToNrrd",
        options: [{ value: "FSLToNrrd", label: "FSL to NRRD (FSLToNrrd)" }],
      },
      {
        name: "allow_lossy",
        label: "Allow lossy conversion (--allowLossyConversion)",
        type: "checkbox",
        default: false,
      },
    ],
  },
  "slicer-dwi-mask": {
    moduleName: "DiffusionWeightedVolumeMasking",
    batchDriverRole: "dwi",
    launchName: "DiffusionWeightedVolumeMasking",
    summary:
      "Generate a brain mask and baseline NRRD volume from a DWI NRRD (e.g. after DWIConvert).",
    docsUrl: "https://slicer.readthedocs.io/en/latest/",
    docsLabel: "3D Slicer documentation",
    estimatedHours: 0.1,
    prerequisites: [
      {
        text: "Convert your FSL DWI to NRRD with DWIConvert first.",
        moduleId: "slicer-dwi-convert",
      },
    ],
    inputs: [
      {
        role: "dwi",
        label: "DWI volume (NRRD)",
        required: true,
        accept: ".nrrd",
        multiple: true,
      },
    ],
    params: [
      {
        name: "remove_islands",
        label: "Remove islands (--removeislands)",
        type: "checkbox",
        default: true,
      },
    ],
  },
  "slicer-dwi-to-dti": {
    moduleName: "DWIToDTIEstimation",
    batchDriverRole: "dwi",
    launchName: "DWIToDTIEstimation",
    summary:
      "Estimate a diffusion tensor volume (DTI NRRD) from DWI, brain mask, and baseline volumes.",
    docsUrl: "https://slicer.readthedocs.io/en/latest/",
    docsLabel: "3D Slicer documentation",
    estimatedHours: 0.25,
    prerequisites: [
      {
        text: "Run DiffusionWeightedVolumeMasking to obtain baseline and brain mask NRRD files.",
        moduleId: "slicer-dwi-mask",
      },
    ],
    inputs: [
      {
        role: "dwi",
        label: "DWI volume (NRRD)",
        required: true,
        accept: ".nrrd",
        multiple: true,
      },
      {
        role: "baseline",
        label: "Baseline volume (NRRD, shared)",
        required: true,
        accept: ".nrrd",
        multiple: false,
      },
      {
        role: "mask",
        label: "Brain mask (NRRD, shared)",
        required: true,
        accept: ".nrrd",
        multiple: false,
      },
    ],
    params: [
      {
        name: "enumeration",
        label: "Estimation method (--enumeration)",
        type: "select",
        default: "LS",
        options: [{ value: "LS", label: "Least squares (LS)" }],
      },
    ],
  },
};

if (typeof window !== "undefined") {
  window.SLICER_MODULES = SLICER_MODULES;
}

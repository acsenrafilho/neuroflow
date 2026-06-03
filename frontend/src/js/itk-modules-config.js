/**
 * ITK module metadata for read-only module pages (host setup and documentation).
 * @type {Record<string, object>}
 */
const ITK_MODULES = {
  "itk-diffusion-complexity-mapping": {
    moduleName: "Diffusion Complexity Mapping",
    runnable: true,
    batchDriverRole: "input",
    summary:
      "Assess biological self-organization patterns in diffusion MRI using diffusion complexity mapping (CSIM ITK Features).",
    docsUrl: "https://github.com/CSIM-Toolkits/ITK/tree/master",
    docsLabel: "CSIM ITK repository",
    availabilityMode: "itk_binary",
    estimatedHours: 0.5,
    setupHint:
      "Binary path is read from config/itk-binaries.json (see config/itk-binaries.example.json).",
    configKey: "itk-diffusion-complexity-mapping",
    cliHint:
      "DiffusionComplexityMapping <input> [<mask> <output> <q>] or <input> <output> <q> without mask",
    prerequisites: [],
    inputs: [
      {
        role: "input",
        label: "DWI / vector image (ITK VectorImage)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "mask",
        label: "Diffusion mask (optional)",
        required: false,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
    ],
    params: [
      {
        name: "q_value",
        label: "Q value",
        type: "number",
        default: 1.0,
        min: 0,
        step: 0.01,
      },
      {
        name: "use_mask",
        label: "Use diffusion mask (4-argument CLI)",
        type: "checkbox",
        default: true,
      },
    ],
  },
  "itk-anisotropic-anomalous-diffusion": {
    moduleName: "Anisotropic Anomalous Diffusion Image Filter",
    summary:
      "Anisotropic anomalous diffusion (AAD) image denoising filter from the CSIM ITK Filtering module.",
    docsUrl: "https://github.com/CSIM-Toolkits/ITK/tree/master",
    docsLabel: "CSIM ITK repository",
    availabilityMode: "itk_binary",
    setupHint:
      "Compile the AAD filter locally, then register its absolute executable path in config/itk-binaries.json.",
    configKey: "itk-anisotropic-anomalous-diffusion",
  },
  "itk-simple-filter": {
    moduleName: "Simple Filters",
    summary:
      "Simple interface to hundreds of basic and advanced ITK filters inside 3D Slicer (morphology, denoising, thresholding, FFT, region growing, and more).",
    docsUrl:
      "https://slicer.readthedocs.io/en/latest/user_guide/modules/simplefilters.html",
    docsLabel: "Simple Filters — 3D Slicer documentation",
    availabilityMode: "worker_package",
    workerPackageName: "3D Slicer",
    builtInSlicerModule: true,
    slicerMenuPath: "Filtering → Simple Filters",
    overview:
      "The Simple Filters module provides a simple interface to hundreds of basic and advanced filters from ITK. Algorithms include binary and grayscale morphology, denoising, thresholding, intensity manipulation, region growing, FFT, and many advanced filters.",
    panels: [
      {
        name: "Filters",
        description:
          "Select one of the available ITK filters. Use the Search box to find a filter by name quickly.",
      },
      {
        name: "Parameters",
        description:
          "Updates dynamically for the filter selected above: input volumes, filter parameters, and the output image selector.",
      },
      {
        name: "Apply",
        description: "Runs the selected filter with the current parameters.",
      },
      {
        name: "Cancel",
        description: "Stops a filter that is currently running.",
      },
      {
        name: "Restore Defaults",
        description: "Reverts filter parameters to their initial settings.",
      },
      {
        name: "LabelMap",
        description:
          "Checkbox indicating whether the selected output volume is a label map (helps verify the output volume type for the result).",
      },
    ],
    notes: [
      "Most filters that take more than one image expect the same pixel type and the same physical space for all inputs.",
    ],
    tips: [
      "Many filters only work on float pixel type. If you see an error such as “Pixel type: … integer is not supported”, convert the volume to float using the Cast Scalar Volume module in Slicer first.",
    ],
    setupHint:
      "Simple Filters is included with 3D Slicer (no separate extension). Ensure Slicer is installed and discoverable via NEUROFLOW_SLICER_HOME or SLICER_HOME — same as the NeuroFlow 3D Slicer package.",
    docsImageUrl:
      "https://github.com/Slicer/Slicer/releases/download/docs-resources/module_simplefilters.png",
  },
};

if (typeof window !== "undefined") {
  window.ITK_MODULES = ITK_MODULES;
}

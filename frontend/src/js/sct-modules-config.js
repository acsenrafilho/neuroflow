/**
 * SCT module metadata: prerequisites, inputs, parameters, and CLI preview hints.
 * @type {Record<string, object>}
 */
const SCT_MODULES = {
  "sct-deepseg": {
    moduleName: "sct_deepseg",
    batchDriverRole: "input",
    summary:
      "Deep-learning segmentation of the spinal cord (or other tasks). Default task is contrast-agnostic spinalcord.",
    docsUrl: "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_deepseg.html",
    docsLabel: "sct_deepseg documentation",
    estimatedHours: 0.15,
    prerequisites: [],
    inputs: [
      {
        role: "input",
        label: "Anatomical image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "task",
        label: "Segmentation task",
        type: "select",
        default: "spinalcord",
        options: [
          { value: "spinalcord", label: "spinalcord (contrast-agnostic)" },
          { value: "graymatter", label: "graymatter" },
          { value: "lesion_ms", label: "lesion_ms" },
          { value: "lesion_sci_t2", label: "lesion_sci_t2" },
          { value: "sc_lumbar_t2", label: "sc_lumbar_t2" },
          { value: "rootlets", label: "rootlets" },
        ],
      },
    ],
  },
  "sct-propseg": {
    moduleName: "sct_propseg",
    batchDriverRole: "input",
    summary: "Propagation-based spinal cord segmentation (PropSeg).",
    docsUrl: "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_propseg.html",
    docsLabel: "sct_propseg documentation",
    estimatedHours: 0.1,
    prerequisites: [],
    inputs: [
      {
        role: "input",
        label: "Anatomical image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "contrast",
        label: "Contrast (-c)",
        type: "select",
        default: "t2",
        options: [
          { value: "t1", label: "t1" },
          { value: "t2", label: "t2" },
          { value: "t2s", label: "t2s" },
          { value: "dwi", label: "dwi" },
        ],
      },
    ],
  },
  "sct-get-centerline": {
    moduleName: "sct_get_centerline",
    batchDriverRole: "input",
    summary: "Extract the spinal cord centerline from an anatomical image or segmentation.",
    docsUrl:
      "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_get_centerline.html",
    docsLabel: "sct_get_centerline documentation",
    estimatedHours: 0.05,
    prerequisites: [],
    inputs: [
      {
        role: "input",
        label: "Image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "method",
        label: "Method (-method)",
        type: "select",
        default: "optic",
        options: [
          { value: "optic", label: "optic (automatic)" },
          { value: "fitseg", label: "fitseg (from segmentation)" },
        ],
      },
      {
        name: "contrast",
        label: "Contrast (-c)",
        type: "select",
        default: "t2",
        options: [
          { value: "t1", label: "t1" },
          { value: "t2", label: "t2" },
          { value: "t2s", label: "t2s" },
          { value: "dwi", label: "dwi" },
        ],
      },
    ],
  },
  "sct-create-mask": {
    moduleName: "sct_create_mask",
    batchDriverRole: "input",
    summary: "Create a mask along the superior-inferior axis (center of FOV or along a centerline).",
    docsUrl: "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_create_mask.html",
    docsLabel: "sct_create_mask documentation",
    estimatedHours: 0.02,
    prerequisites: [
      {
        text: "For centerline mode, provide a centerline or segmentation image.",
        moduleId: "sct-get-centerline",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "Reference image(s) (NIfTI header)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "centerline",
        label: "Centerline / segmentation (optional, for centerline mode)",
        required: false,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
    ],
    params: [
      {
        name: "process",
        label: "Process mode (-p)",
        type: "select",
        default: "center",
        options: [
          { value: "center", label: "center (middle of FOV)" },
          { value: "centerline", label: "centerline (requires centerline file)" },
        ],
      },
      {
        name: "shape",
        label: "Shape (-f)",
        type: "select",
        default: "cylinder",
        options: [
          { value: "cylinder", label: "cylinder" },
          { value: "box", label: "box" },
          { value: "gaussian", label: "gaussian" },
        ],
      },
      {
        name: "size",
        label: "Size (-size)",
        type: "text",
        default: "41",
      },
    ],
  },
  "sct-label-vertebrae": {
    moduleName: "sct_label_vertebrae",
    batchDriverRole: "input",
    summary: "Label vertebral levels from an anatomical image and cord segmentation.",
    docsUrl:
      "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_label_vertebrae.html",
    docsLabel: "sct_label_vertebrae documentation",
    estimatedHours: 0.25,
    prerequisites: [
      {
        text: "Run spinal cord segmentation first (e.g. sct_deepseg).",
        moduleId: "sct-deepseg",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "Anatomical image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "seg",
        label: "Cord segmentation(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "contrast",
        label: "Contrast (-c)",
        type: "select",
        default: "t2",
        options: [
          { value: "t1", label: "t1" },
          { value: "t2", label: "t2" },
        ],
      },
    ],
  },
  "sct-register-to-template": {
    moduleName: "sct_register_to_template",
    batchDriverRole: "input",
    summary: "Register an anatomical image to the PAM50 spinal cord template.",
    docsUrl:
      "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_register_to_template.html",
    docsLabel: "sct_register_to_template documentation",
    estimatedHours: 0.5,
    prerequisites: [
      {
        text: "Provide cord segmentation; vertebral labels improve alignment when available.",
        moduleId: "sct-label-vertebrae",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "Anatomical image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "seg",
        label: "Cord segmentation(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "labels",
        label: "Vertebral labels (optional)",
        required: false,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
    ],
    params: [
      {
        name: "contrast",
        label: "Contrast (-c)",
        type: "select",
        default: "t2",
        options: [
          { value: "t1", label: "t1" },
          { value: "t2", label: "t2" },
          { value: "t2s", label: "t2s" },
        ],
      },
    ],
  },
  "sct-warp-template": {
    moduleName: "sct_warp_template",
    batchDriverRole: "dest",
    summary: "Warp the PAM50 template and atlases to a destination image using a warping field.",
    docsUrl: "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_warp_template.html",
    docsLabel: "sct_warp_template documentation",
    estimatedHours: 0.1,
    prerequisites: [
      {
        text: "Obtain a warping field from sct_register_to_template (or multimodal registration).",
        moduleId: "sct-register-to-template",
      },
    ],
    inputs: [
      {
        role: "dest",
        label: "Destination image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "warp",
        label: "Warping field(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [],
  },
  "sct-apply-transfo": {
    moduleName: "sct_apply_transfo",
    batchDriverRole: "input",
    summary: "Apply warping fields or affine transforms to an image.",
    docsUrl: "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_apply_transfo.html",
    docsLabel: "sct_apply_transfo documentation",
    estimatedHours: 0.05,
    prerequisites: [],
    inputs: [
      {
        role: "input",
        label: "Input image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "dest",
        label: "Destination / reference image",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
      {
        role: "warp",
        label: "Transform / warping field",
        required: true,
        accept: ".nii,.nii.gz,.txt,.mat",
        multiple: false,
      },
    ],
    params: [
      {
        name: "interpolation",
        label: "Interpolation (-x)",
        type: "select",
        default: "linear",
        options: [
          { value: "nn", label: "nn (nearest neighbor)" },
          { value: "linear", label: "linear" },
          { value: "spline", label: "spline" },
          { value: "label", label: "label" },
        ],
      },
    ],
  },
  "sct-process-segmentation": {
    moduleName: "sct_process_segmentation",
    batchDriverRole: "input",
    summary: "Compute CSA and other morphometrics from a spinal cord segmentation.",
    docsUrl:
      "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_process_segmentation.html",
    docsLabel: "sct_process_segmentation documentation",
    estimatedHours: 0.05,
    prerequisites: [
      {
        text: "Run cord segmentation first (e.g. sct_deepseg or sct_propseg).",
        moduleId: "sct-deepseg",
      },
      {
        text: "For CSA at C1–C3, provide vertebral labels from sct_label_vertebrae (vertfile) with -vert and -perlevel.",
        moduleId: "sct-label-vertebrae",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "Cord segmentation(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "vertfile",
        label: "Vertebral label file (required with -vert / -perlevel)",
        required: false,
        accept: ".nii,.nii.gz",
        multiple: false,
      },
    ],
    params: [
      {
        name: "perslice",
        label: "Per-slice metrics (-perslice)",
        type: "select",
        default: "0",
        options: [
          { value: "0", label: "0 (off)" },
          { value: "1", label: "1 (on)" },
        ],
      },
      {
        name: "vert",
        label: "Vertebral levels (-vert)",
        type: "text",
        default: "1:3",
      },
      {
        name: "perlevel",
        label: "Per-level metrics (-perlevel)",
        type: "select",
        default: "1",
        options: [
          { value: "0", label: "0 (average across levels)" },
          { value: "1", label: "1 (one row per vertebral level)" },
        ],
      },
      {
        name: "angle_corr",
        label: "Angle correction (-angle-corr)",
        type: "select",
        default: "1",
        options: [
          { value: "1", label: "1 (on)" },
          { value: "0", label: "0 (off)" },
        ],
      },
    ],
  },
  "sct-qc": {
    moduleName: "sct_qc",
    batchDriverRole: "input",
    summary:
      "Generate an HTML QC report (PNG overlays) for cord segmentation or vertebral labels. Open index.html on disk; NeuroFlow does not embed an image viewer.",
    docsUrl: "https://spinalcordtoolbox.com/stable/user_section/command-line/sct_qc.html",
    docsLabel: "sct_qc documentation",
    estimatedHours: 0.05,
    prerequisites: [
      {
        text: "Run cord segmentation first (sct_deepseg). Use process sct_deepseg_sc for that QC.",
        moduleId: "sct-deepseg",
      },
      {
        text: "For label QC, run sct_label_vertebrae and upload the labeled segmentation as -s.",
        moduleId: "sct-label-vertebrae",
      },
    ],
    inputs: [
      {
        role: "input",
        label: "Anatomical image(s) (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
      {
        role: "seg",
        label: "Segmentation or vertebral labels (NIfTI)",
        required: true,
        accept: ".nii,.nii.gz",
        multiple: true,
      },
    ],
    params: [
      {
        name: "process",
        label: "QC process (-p)",
        type: "select",
        default: "sct_deepseg_sc",
        options: [
          { value: "sct_deepseg_sc", label: "sct_deepseg_sc (cord segmentation)" },
          { value: "sct_label_vertebrae", label: "sct_label_vertebrae (vertebral labels)" },
        ],
      },
    ],
  },
};

if (typeof window !== "undefined") {
  window.SCT_MODULES = SCT_MODULES;
}

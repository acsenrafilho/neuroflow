/**
 * Resolve NeuroFlow API base (same host or local uvicorn on :8000).
 * Caches the first working base in sessionStorage.
 */
(function (global) {
  const STORAGE_KEY = "neuroflow_api_base";

  const MODULES_FALLBACK = [
    {
      id: "freesurfer-recon-all",
      package_id: "freesurfer",
      package_name: "FreeSurfer",
      module_name: "recon-all (-all)",
      description: "Full cortical reconstruction pipeline from T1-weighted MRI.",
      page_path: "/tools/freesurfer.html",
      recon_options: "all",
      estimated_hours_per_scan: 8,
      coming_soon: false,
      available: false,
    },
    {
      id: "freesurfer-autorecon1",
      package_id: "freesurfer",
      package_name: "FreeSurfer",
      module_name: "autorecon1",
      description: "Motion correction and intensity normalization (recon-all -autorecon1).",
      page_path: "/tools/freesurfer.html",
      recon_options: "autorecon1",
      estimated_hours_per_scan: 1,
      coming_soon: false,
      available: false,
    },
    {
      id: "freesurfer-autorecon2",
      package_id: "freesurfer",
      package_name: "FreeSurfer",
      module_name: "autorecon2",
      description: "Subcortical segmentation stage (recon-all -autorecon2).",
      page_path: "/tools/freesurfer.html",
      recon_options: "autorecon2",
      estimated_hours_per_scan: 2,
      coming_soon: false,
      available: false,
    },
    {
      id: "freesurfer-autorecon3",
      package_id: "freesurfer",
      package_name: "FreeSurfer",
      module_name: "autorecon3",
      description: "Cortical surface reconstruction (recon-all -autorecon3).",
      page_path: "/tools/freesurfer.html",
      recon_options: "autorecon3",
      estimated_hours_per_scan: 3,
      coming_soon: false,
      available: false,
    },
    {
      id: "fsl-bet",
      package_id: "fsl",
      package_name: "FSL",
      module_name: "BET",
      description: "Brain Extraction Tool (BET and BET2).",
      page_path: "/tools/fsl.html",
      recon_options: null,
      estimated_hours_per_scan: 0.05,
      coming_soon: false,
      available: false,
    },
    {
      id: "fsl-fast",
      package_id: "fsl",
      package_name: "FSL",
      module_name: "FAST",
      description: "Tissue-class segmentation.",
      page_path: "/tools/fsl.html",
      recon_options: null,
      estimated_hours_per_scan: 0.25,
      coming_soon: false,
      available: false,
    },
    {
      id: "fsl-flirt",
      package_id: "fsl",
      package_name: "FSL",
      module_name: "FLIRT",
      description: "Linear registration.",
      page_path: "/tools/fsl.html",
      recon_options: null,
      estimated_hours_per_scan: 0.1,
      coming_soon: false,
      available: false,
    },
    {
      id: "fsl-mcflirt",
      package_id: "fsl",
      package_name: "FSL",
      module_name: "MCFLIRT",
      description: "Motion correction for 4D series.",
      page_path: "/tools/fsl.html",
      recon_options: null,
      estimated_hours_per_scan: 0.25,
      coming_soon: false,
      available: false,
    },
    {
      id: "ants-placeholder",
      package_id: "ants",
      package_name: "ANTs",
      module_name: "—",
      description:
        "Advanced Normalization Tools — registration and segmentation — coming soon.",
      page_path: "/tools/ants.html",
      recon_options: null,
      estimated_hours_per_scan: 1,
      coming_soon: true,
      available: false,
    },
    {
      id: "slicer-dwi-convert",
      package_id: "slicer",
      package_name: "3D Slicer",
      module_name: "DWIConvert",
      description: "Convert FSL-format DWI to NRRD for Slicer diffusion tools.",
      page_path: "/tools/slicer.html",
      recon_options: null,
      estimated_hours_per_scan: 0.1,
      coming_soon: false,
      available: false,
    },
    {
      id: "slicer-dwi-mask",
      package_id: "slicer",
      package_name: "3D Slicer",
      module_name: "DiffusionWeightedVolumeMasking",
      description: "Generate brain mask and baseline NRRD from DWI.",
      page_path: "/tools/slicer.html",
      recon_options: null,
      estimated_hours_per_scan: 0.1,
      coming_soon: false,
      available: false,
    },
    {
      id: "slicer-dwi-to-dti",
      package_id: "slicer",
      package_name: "3D Slicer",
      module_name: "DWIToDTIEstimation",
      description: "Estimate DTI volume from DWI, mask, and baseline.",
      page_path: "/tools/slicer.html",
      recon_options: null,
      estimated_hours_per_scan: 0.25,
      coming_soon: false,
      available: false,
    },
    {
      id: "itk-diffusion-complexity-mapping",
      package_id: "itk",
      package_name: "ITK",
      module_name: "Diffusion Complexity Mapping",
      description: "Diffusion complexity mapping from diffusion MRI (CSIM ITK).",
      page_path: "/tools/itk.html",
      recon_options: null,
      estimated_hours_per_scan: 0.5,
      coming_soon: false,
      available: false,
    },
    {
      id: "itk-anisotropic-anomalous-diffusion",
      package_id: "itk",
      package_name: "ITK",
      module_name: "Anisotropic Anomalous Diffusion Image Filter",
      description: "Anisotropic anomalous diffusion denoising (CSIM ITK AAD).",
      page_path: "/tools/itk.html",
      recon_options: null,
      estimated_hours_per_scan: 0.25,
      coming_soon: false,
      available: false,
    },
    {
      id: "itk-simple-filter",
      package_id: "itk",
      package_name: "ITK",
      module_name: "Simple Filters",
      description: "Hundreds of ITK filters via built-in 3D Slicer Simple Filters module.",
      page_path: "/tools/itk.html",
      recon_options: null,
      estimated_hours_per_scan: 0.1,
      coming_soon: false,
      available: false,
    },
  ];

  function candidateBases() {
    const cached = sessionStorage.getItem(STORAGE_KEY);
    const bases = [
      cached,
      global.location.origin,
      "http://127.0.0.1:8000",
      "http://localhost:8000",
    ];
    return [...new Set(bases.filter(Boolean))];
  }

  async function fetchApi(path, options) {
    let lastError = null;
    for (const base of candidateBases()) {
      try {
        const res = await fetch(`${base}${path}`, options);
        if (res.ok) {
          sessionStorage.setItem(STORAGE_KEY, base);
          return { res, base };
        }
        lastError = new Error(`HTTP ${res.status}`);
      } catch (err) {
        lastError = err;
      }
    }
    throw lastError || new Error("API unavailable");
  }

  async function fetchJson(path, options) {
    const { res } = await fetchApi(path, options);
    return res.json();
  }

  async function getApiBase() {
    const cached = sessionStorage.getItem(STORAGE_KEY);
    if (cached) return cached;
    const { base } = await fetchApi("/api/v1/health");
    return base;
  }

  global.NeuroflowApi = {
    MODULES_FALLBACK,
    candidateBases,
    fetchApi,
    fetchJson,
    getApiBase,
  };
})(window);

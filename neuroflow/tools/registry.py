"""Registered neuroimaging tools and processing modules exposed in the portal."""

from dataclasses import dataclass
from typing import Literal

ReconOption = Literal["all", "autorecon1", "autorecon2", "autorecon3"]
AvailabilityMode = Literal["package", "itk_binary", "worker_package"]


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    description: str
    page_path: str
    executable: str | None = None
    probe_binaries: tuple[str, ...] = ()
    visible_in_portal: bool = True

    def is_available(self) -> bool:
        from neuroflow.config import get_settings
        from neuroflow.tools.host_probe import probe_package

        return probe_package(get_settings(), self.id).available


@dataclass(frozen=True)
class ModuleDefinition:
    id: str
    package_id: str
    package_name: str
    module_name: str
    description: str
    page_path: str
    recon_options: ReconOption | None = None
    estimated_hours_per_scan: float = 1.0
    coming_soon: bool = False
    required_executable: str | None = None
    availability_mode: AvailabilityMode = "package"
    worker_package_id: str | None = None


TOOLS: dict[str, ToolDefinition] = {
    "freesurfer": ToolDefinition(
        id="freesurfer",
        name="FreeSurfer",
        description="Cortical reconstruction and volumetric segmentation (recon-all).",
        page_path="/tools/freesurfer.html",
        executable="recon-all",
    ),
    "fsl": ToolDefinition(
        id="fsl",
        name="FSL",
        description="FMRIB Software Library — structural, diffusion, and registration tools.",
        page_path="/tools/fsl.html",
        executable="bet",
        probe_binaries=(
            "bet",
            "bet2",
            "fast",
            "flirt",
            "fnirt",
            "topup",
            "eddy",
            "eddy_openmp",
            "dtifit",
        ),
    ),
    "ants": ToolDefinition(
        id="ants",
        name="ANTs",
        description=(
            "Advanced Normalization Tools — registration, segmentation, "
            "bias correction, and image utilities."
        ),
        page_path="/tools/ants.html",
        executable="antsRegistration",
        probe_binaries=(
            "antsRegistration",
            "antsApplyTransforms",
            "N4BiasFieldCorrection",
            "Atropos",
        ),
        visible_in_portal=False,
    ),
    "slicer": ToolDefinition(
        id="slicer",
        name="3D Slicer",
        description="3D Slicer CLI modules for diffusion MRI (DWI pipeline).",
        page_path="/tools/slicer.html",
        executable="Slicer",
        probe_binaries=("Slicer", "slicer"),
        visible_in_portal=False,
    ),
    "itk": ToolDefinition(
        id="itk",
        name="ITK",
        description=(
            "CSIM ITK toolkits — locally compiled filters and Slicer-backed Simple Filters."
        ),
        page_path="/tools/itk.html",
        visible_in_portal=False,
    ),
    "sct": ToolDefinition(
        id="sct",
        name="Spinal Cord Toolbox",
        description=(
            "Spinal Cord Toolbox (SCT) — segmentation, labeling, template registration, "
            "and morphometrics for spinal cord MRI."
        ),
        page_path="/tools/sct.html",
        executable="sct_version",
        probe_binaries=(
            "sct_version",
            "sct_deepseg",
            "sct_propseg",
            "sct_get_centerline",
            "sct_create_mask",
            "sct_label_vertebrae",
            "sct_register_to_template",
            "sct_warp_template",
            "sct_apply_transfo",
            "sct_process_segmentation",
        ),
    ),
}

MODULES: tuple[ModuleDefinition, ...] = (
    ModuleDefinition(
        id="freesurfer-recon-all",
        package_id="freesurfer",
        package_name="FreeSurfer",
        module_name="recon-all (-all)",
        description="Full cortical reconstruction pipeline from T1-weighted MRI.",
        page_path="/tools/freesurfer.html",
        recon_options="all",
        estimated_hours_per_scan=8.0,
    ),
    ModuleDefinition(
        id="freesurfer-autorecon1",
        package_id="freesurfer",
        package_name="FreeSurfer",
        module_name="autorecon1",
        description="Motion correction and intensity normalization (recon-all -autorecon1).",
        page_path="/tools/freesurfer.html",
        recon_options="autorecon1",
        estimated_hours_per_scan=1.0,
    ),
    ModuleDefinition(
        id="freesurfer-autorecon2",
        package_id="freesurfer",
        package_name="FreeSurfer",
        module_name="autorecon2",
        description="Subcortical segmentation stage (recon-all -autorecon2).",
        page_path="/tools/freesurfer.html",
        recon_options="autorecon2",
        estimated_hours_per_scan=2.0,
    ),
    ModuleDefinition(
        id="freesurfer-autorecon3",
        package_id="freesurfer",
        package_name="FreeSurfer",
        module_name="autorecon3",
        description="Cortical surface reconstruction (recon-all -autorecon3).",
        page_path="/tools/freesurfer.html",
        recon_options="autorecon3",
        estimated_hours_per_scan=3.0,
    ),
    ModuleDefinition(
        id="fsl-bet",
        package_id="fsl",
        package_name="FSL",
        module_name="BET",
        description="Brain Extraction Tool (BET and BET2) for skull-stripping structural images.",
        page_path="/tools/fsl.html",
        required_executable="bet",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="fsl-fast",
        package_id="fsl",
        package_name="FSL",
        module_name="FAST",
        description="FMRIB's Automated Segmentation Tool for tissue-class segmentation.",
        page_path="/tools/fsl.html",
        required_executable="fast",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="fsl-first",
        package_id="fsl",
        package_name="FSL",
        module_name="FIRST",
        description="Model-based subcortical structure segmentation.",
        page_path="/tools/fsl.html",
        required_executable="run_first_all",
        estimated_hours_per_scan=1.0,
    ),
    ModuleDefinition(
        id="fsl-bianca",
        package_id="fsl",
        package_name="FSL",
        module_name="BIANCA",
        description="White-matter hyperintensity classification (feature-file based).",
        page_path="/tools/fsl.html",
        required_executable="bianca",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="fsl-siena",
        package_id="fsl",
        package_name="FSL",
        module_name="SIENA",
        description="Structural brain change analysis between two time-point T1 scans.",
        page_path="/tools/fsl.html",
        required_executable="siena",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="fsl-eddy",
        package_id="fsl",
        package_name="FSL",
        module_name="EDDY",
        description="Eddy-current and movement correction for diffusion MRI.",
        page_path="/tools/fsl.html",
        required_executable="eddy",
        estimated_hours_per_scan=1.0,
    ),
    ModuleDefinition(
        id="fsl-topup",
        package_id="fsl",
        package_name="FSL",
        module_name="TOPUP",
        description="Distortion correction from opposing phase-encode diffusion data.",
        page_path="/tools/fsl.html",
        required_executable="topup",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="fsl-fdt",
        package_id="fsl",
        package_name="FSL",
        module_name="FDT (dtifit)",
        description="Diffusion tensor fitting (dtifit) for DTI parameter maps.",
        page_path="/tools/fsl.html",
        required_executable="dtifit",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="fsl-bedpostx",
        package_id="fsl",
        package_name="FSL",
        module_name="BEDPOSTX",
        description="Bayesian estimation of diffusion parameters (multi-fibre bedpostX).",
        page_path="/tools/fsl.html",
        required_executable="bedpostx",
        estimated_hours_per_scan=4.0,
    ),
    ModuleDefinition(
        id="fsl-tbss",
        package_id="fsl",
        package_name="FSL",
        module_name="TBSS",
        description="Tract-Based Spatial Statistics — step 1 pre-processing (tbss_1_preproc).",
        page_path="/tools/fsl.html",
        required_executable="tbss_1_preproc",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="fsl-flirt",
        package_id="fsl",
        package_name="FSL",
        module_name="FLIRT",
        description="Linear image registration.",
        page_path="/tools/fsl.html",
        required_executable="flirt",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="fsl-fnirt",
        package_id="fsl",
        package_name="FSL",
        module_name="FNIRT",
        description="Non-linear registration (requires FLIRT affine matrix).",
        page_path="/tools/fsl.html",
        required_executable="fnirt",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="fsl-susan",
        package_id="fsl",
        package_name="FSL",
        module_name="SUSAN",
        description="Smallest Univalue Segment Assimilating Nucleus noise reduction.",
        page_path="/tools/fsl.html",
        required_executable="susan",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="fsl-epi-reg",
        package_id="fsl",
        package_name="FSL",
        module_name="epi_reg",
        description="EPI to structural registration.",
        page_path="/tools/fsl.html",
        required_executable="epi_reg",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="fsl-mcflirt",
        package_id="fsl",
        package_name="FSL",
        module_name="MCFLIRT",
        description="Motion correction for fMRI or diffusion time series.",
        page_path="/tools/fsl.html",
        required_executable="mcflirt",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="ants-n4",
        package_id="ants",
        package_name="ANTs",
        module_name="N4BiasFieldCorrection",
        description="N4 bias field correction for structural MRI (inhomogeneity correction).",
        page_path="/tools/ants.html",
        required_executable="N4BiasFieldCorrection",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="ants-registration",
        package_id="ants",
        package_name="ANTs",
        module_name="antsRegistration",
        description="Deformable or rigid registration between fixed and moving images.",
        page_path="/tools/ants.html",
        required_executable="antsRegistration",
        estimated_hours_per_scan=1.0,
    ),
    ModuleDefinition(
        id="ants-apply-transforms",
        package_id="ants",
        package_name="ANTs",
        module_name="antsApplyTransforms",
        description="Apply transforms to warp images, masks, or point sets.",
        page_path="/tools/ants.html",
        required_executable="antsApplyTransforms",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="ants-registration-syn",
        package_id="ants",
        package_name="ANTs",
        module_name="antsRegistrationSyN",
        description="SyN registration pipeline script with default multi-stage parameters.",
        page_path="/tools/ants.html",
        required_executable="antsRegistrationSyN.sh",
        estimated_hours_per_scan=1.0,
    ),
    ModuleDefinition(
        id="ants-registration-syn-quick",
        package_id="ants",
        package_name="ANTs",
        module_name="antsRegistrationSyNQuick",
        description="Fast SyN pairwise registration (recommended quick deformable registration).",
        page_path="/tools/ants.html",
        required_executable="antsRegistrationSyNQuick.sh",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="ants-atropos",
        package_id="ants",
        package_name="ANTs",
        module_name="Atropos",
        description="EM segmentation with optional spatial priors and masks.",
        page_path="/tools/ants.html",
        required_executable="Atropos",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="ants-image-math",
        package_id="ants",
        package_name="ANTs",
        module_name="ImageMath",
        description="ImageMath utilities (whitelisted operations on uploaded volumes).",
        page_path="/tools/ants.html",
        required_executable="ImageMath",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="ants-sccan",
        package_id="ants",
        package_name="ANTs",
        module_name="sccan",
        description="Sparse canonical correlation analysis for multivariate imaging data.",
        page_path="/tools/ants.html",
        required_executable="sccan",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="ants-kelly-kapowski",
        package_id="ants",
        package_name="ANTs",
        module_name="KellyKapowski",
        description="Cortical thickness estimation (KellyKapowski pipeline).",
        page_path="/tools/ants.html",
        required_executable="KellyKapowski",
        estimated_hours_per_scan=1.0,
    ),
    ModuleDefinition(
        id="ants-motion-corr",
        package_id="ants",
        package_name="ANTs",
        module_name="antsMotionCorr",
        description="Motion correction for 4D time series (e.g. fMRI or DWI).",
        page_path="/tools/ants.html",
        required_executable="antsMotionCorr",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="ants-denoise",
        package_id="ants",
        package_name="ANTs",
        module_name="DenoiseImage",
        description="Non-local means denoising of structural or diffusion images.",
        page_path="/tools/ants.html",
        required_executable="DenoiseImage",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="ants-transform-info",
        package_id="ants",
        package_name="ANTs",
        module_name="antsTransformInfo",
        description="Inspect transform files (affine, warp, composite).",
        page_path="/tools/ants.html",
        required_executable="antsTransformInfo",
        estimated_hours_per_scan=0.02,
    ),
    ModuleDefinition(
        id="ants-jacobian",
        package_id="ants",
        package_name="ANTs",
        module_name="CreateJacobianDeterminantImage",
        description="Jacobian determinant image from a deformation field warp.",
        page_path="/tools/ants.html",
        required_executable="CreateJacobianDeterminantImage",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="ants-cortical-thickness",
        package_id="ants",
        package_name="ANTs",
        module_name="antsCorticalThickness",
        description="Cortical thickness pipeline (requires template and prior images).",
        page_path="/tools/ants.html",
        required_executable="antsCorticalThickness.sh",
        estimated_hours_per_scan=4.0,
    ),
    ModuleDefinition(
        id="ants-brain-extraction",
        package_id="ants",
        package_name="ANTs",
        module_name="antsBrainExtraction",
        description="Skull-stripping / brain extraction with atlas templates.",
        page_path="/tools/ants.html",
        required_executable="antsBrainExtraction.sh",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="ants-template-construction",
        package_id="ants",
        package_name="ANTs",
        module_name="antsMultivariateTemplateConstruction2",
        description="Multivariate template construction from a cohort of images.",
        page_path="/tools/ants.html",
        required_executable="antsMultivariateTemplateConstruction2.sh",
        estimated_hours_per_scan=8.0,
    ),
    ModuleDefinition(
        id="ants-resample",
        package_id="ants",
        package_name="ANTs",
        module_name="ResampleImage",
        description="Resample image to reference space or spacing.",
        page_path="/tools/ants.html",
        required_executable="ResampleImage",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="ants-threshold",
        package_id="ants",
        package_name="ANTs",
        module_name="ThresholdImage",
        description="Threshold image intensities.",
        page_path="/tools/ants.html",
        required_executable="ThresholdImage",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="ants-smooth",
        package_id="ants",
        package_name="ANTs",
        module_name="SmoothImage",
        description="Gaussian smoothing of image volumes.",
        page_path="/tools/ants.html",
        required_executable="SmoothImage",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="ants-convert",
        package_id="ants",
        package_name="ANTs",
        module_name="ConvertImage",
        description="Convert image pixel type or dimensionality.",
        page_path="/tools/ants.html",
        required_executable="ConvertImage",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="ants-measure-similarity",
        package_id="ants",
        package_name="ANTs",
        module_name="MeasureImageSimilarity",
        description="Measure similarity between fixed and moving images.",
        page_path="/tools/ants.html",
        required_executable="MeasureImageSimilarity",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="ants-joint-fusion",
        package_id="ants",
        package_name="ANTs",
        module_name="antsJointFusion",
        description="Multi-atlas label fusion segmentation.",
        page_path="/tools/ants.html",
        required_executable="antsJointFusion",
        estimated_hours_per_scan=1.0,
    ),
    ModuleDefinition(
        id="sct-deepseg",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_deepseg",
        description="Deep-learning segmentation of spinal cord or pathologies (task-based).",
        page_path="/tools/sct.html",
        required_executable="sct_deepseg",
        estimated_hours_per_scan=0.15,
    ),
    ModuleDefinition(
        id="sct-propseg",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_propseg",
        description="Propagation-based spinal cord segmentation (PropSeg).",
        page_path="/tools/sct.html",
        required_executable="sct_propseg",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="sct-get-centerline",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_get_centerline",
        description="Extract spinal cord centerline from anatomical or segmented images.",
        page_path="/tools/sct.html",
        required_executable="sct_get_centerline",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="sct-create-mask",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_create_mask",
        description="Create a cylindrical or box mask along the superior-inferior axis.",
        page_path="/tools/sct.html",
        required_executable="sct_create_mask",
        estimated_hours_per_scan=0.02,
    ),
    ModuleDefinition(
        id="sct-label-vertebrae",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_label_vertebrae",
        description="Label vertebral levels from an anatomical image and cord segmentation.",
        page_path="/tools/sct.html",
        required_executable="sct_label_vertebrae",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="sct-register-to-template",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_register_to_template",
        description="Register an anatomical image to the PAM50 spinal cord template.",
        page_path="/tools/sct.html",
        required_executable="sct_register_to_template",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="sct-warp-template",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_warp_template",
        description="Warp the PAM50 template and atlases to a destination image space.",
        page_path="/tools/sct.html",
        required_executable="sct_warp_template",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="sct-apply-transfo",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_apply_transfo",
        description="Apply warping fields or affine transforms to an image.",
        page_path="/tools/sct.html",
        required_executable="sct_apply_transfo",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="sct-process-segmentation",
        package_id="sct",
        package_name="Spinal Cord Toolbox",
        module_name="sct_process_segmentation",
        description="Compute CSA and other morphometrics from a spinal cord segmentation.",
        page_path="/tools/sct.html",
        required_executable="sct_process_segmentation",
        estimated_hours_per_scan=0.05,
    ),
    ModuleDefinition(
        id="slicer-dwi-convert",
        package_id="slicer",
        package_name="3D Slicer",
        module_name="DWIConvert",
        description="Convert FSL-format DWI (NIfTI + bvals/bvecs) to NRRD for Slicer diffusion tools.",
        page_path="/tools/slicer.html",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="slicer-dwi-mask",
        package_id="slicer",
        package_name="3D Slicer",
        module_name="DiffusionWeightedVolumeMasking",
        description="Generate a brain mask and baseline volume from a DWI NRRD volume.",
        page_path="/tools/slicer.html",
        estimated_hours_per_scan=0.1,
    ),
    ModuleDefinition(
        id="slicer-dwi-to-dti",
        package_id="slicer",
        package_name="3D Slicer",
        module_name="DWIToDTIEstimation",
        description="Estimate a diffusion tensor volume (DTI) from DWI, mask, and baseline NRRD inputs.",
        page_path="/tools/slicer.html",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="itk-diffusion-complexity-mapping",
        package_id="itk",
        package_name="ITK",
        module_name="Diffusion Complexity Mapping",
        description=(
            "Diffusion complexity mapping from diffusion MRI (CSIM ITK Features module)."
        ),
        page_path="/tools/itk.html",
        availability_mode="itk_binary",
        estimated_hours_per_scan=0.5,
    ),
    ModuleDefinition(
        id="itk-anisotropic-anomalous-diffusion",
        package_id="itk",
        package_name="ITK",
        module_name="Anisotropic Anomalous Diffusion Image Filter",
        description=(
            "Anisotropic anomalous diffusion denoising filter (CSIM ITK Filtering — AAD)."
        ),
        page_path="/tools/itk.html",
        availability_mode="itk_binary",
        estimated_hours_per_scan=0.25,
    ),
    ModuleDefinition(
        id="itk-simple-filter",
        package_id="itk",
        package_name="ITK",
        module_name="Simple Filters",
        description=(
            "Hundreds of ITK image filters through the built-in 3D Slicer Simple Filters module."
        ),
        page_path="/tools/itk.html",
        availability_mode="worker_package",
        worker_package_id="slicer",
        estimated_hours_per_scan=0.1,
    ),
)


def get_tool(tool_id: str) -> ToolDefinition | None:
    return TOOLS.get(tool_id)


def list_tools(*, portal_only: bool = False) -> list[ToolDefinition]:
    tools = list(TOOLS.values())
    if portal_only:
        tools = [t for t in tools if t.visible_in_portal]
    return tools


def get_module(module_id: str) -> ModuleDefinition | None:
    return next((m for m in MODULES if m.id == module_id), None)


def list_modules(*, portal_only: bool = False) -> list[ModuleDefinition]:
    modules = list(MODULES)
    if portal_only:
        visible_packages = {t.id for t in list_tools(portal_only=True)}
        modules = [m for m in modules if m.package_id in visible_packages]
    return modules


def is_package_visible_in_portal(package_id: str) -> bool:
    tool = get_tool(package_id)
    return bool(tool and tool.visible_in_portal)

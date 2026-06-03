"""Registered neuroimaging tools and processing modules exposed in the portal."""

from dataclasses import dataclass
from typing import Literal

ReconOption = Literal["all", "autorecon1", "autorecon2", "autorecon3"]


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    description: str
    page_path: str
    executable: str | None = None
    probe_binaries: tuple[str, ...] = ()

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
        description="Advanced Normalization Tools (coming soon).",
        page_path="/tools/ants.html",
        executable="antsRegistration",
        probe_binaries=("antsRegistration", "ANTS", "antsApplyTransforms"),
    ),
    "slicer": ToolDefinition(
        id="slicer",
        name="3D Slicer",
        description="3D Slicer CLI modules for diffusion MRI (DWI pipeline).",
        page_path="/tools/slicer.html",
        executable="Slicer",
        probe_binaries=("Slicer", "slicer"),
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
        id="ants-placeholder",
        package_id="ants",
        package_name="ANTs",
        module_name="—",
        description="Advanced Normalization Tools — registration and segmentation — coming soon.",
        page_path="/tools/ants.html",
        coming_soon=True,
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
)


def get_tool(tool_id: str) -> ToolDefinition | None:
    return TOOLS.get(tool_id)


def list_tools() -> list[ToolDefinition]:
    return list(TOOLS.values())


def get_module(module_id: str) -> ModuleDefinition | None:
    return next((m for m in MODULES if m.id == module_id), None)


def list_modules() -> list[ModuleDefinition]:
    return list(MODULES)

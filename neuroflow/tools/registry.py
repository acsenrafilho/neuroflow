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
        description="FMRIB Software Library (coming soon).",
        page_path="/tools/fsl.html",
        executable="bet",
        probe_binaries=("bet", "fsl", "flirt"),
    ),
    "ants": ToolDefinition(
        id="ants",
        name="ANTs",
        description="Advanced Normalization Tools (coming soon).",
        page_path="/tools/ants.html",
        executable="antsRegistration",
        probe_binaries=("antsRegistration", "ANTS", "antsApplyTransforms"),
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
        id="fsl-placeholder",
        package_id="fsl",
        package_name="FSL",
        module_name="—",
        description="FMRIB Software Library (BET, FAST, etc.) — coming soon.",
        page_path="/tools/fsl.html",
        coming_soon=True,
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
)


def get_tool(tool_id: str) -> ToolDefinition | None:
    return TOOLS.get(tool_id)


def list_tools() -> list[ToolDefinition]:
    return list(TOOLS.values())


def get_module(module_id: str) -> ModuleDefinition | None:
    return next((m for m in MODULES if m.id == module_id), None)


def list_modules() -> list[ModuleDefinition]:
    return list(MODULES)

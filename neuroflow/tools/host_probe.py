"""Host-side discovery of installed neuroimaging packages."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from shutil import which

from neuroflow.config import Settings
from neuroflow.tools.base import resolve_executable
from neuroflow.tools.itk_binaries import count_configured_native_binaries, resolve_itk_module_binary
from neuroflow.tools.registry import ModuleDefinition

PACKAGE_IDS: tuple[str, ...] = ("freesurfer", "fsl", "ants", "slicer", "itk", "sct")

_PACKAGE_DISPLAY_NAMES = {
    "freesurfer": "FreeSurfer",
    "fsl": "FSL",
    "ants": "ANTs",
    "slicer": "3D Slicer",
    "itk": "ITK",
    "sct": "Spinal Cord Toolbox",
}

logger = logging.getLogger(__name__)

TOOL_AVAILABILITY_STATE_KEY = "tool_availability"


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of checking one package on the local host."""

    package_id: str
    available: bool
    resolved_path: str | None = None
    detail: str = ""


def _first_on_path(binaries: tuple[str, ...]) -> str | None:
    for name in binaries:
        found = which(name)
        if found:
            return found
    return None


def _env_dir_exists(var_names: tuple[str, ...]) -> str | None:
    for var in var_names:
        value = os.environ.get(var)
        if value and Path(value).is_dir():
            return value
    return None


def probe_freesurfer(settings: Settings) -> ProbeResult:
    resolved = resolve_executable(settings, "recon-all")
    if resolved is not None:
        return ProbeResult(
            package_id="freesurfer",
            available=True,
            resolved_path=str(resolved),
            detail="recon-all found",
        )

    if settings.neuroflow_freesurfer_home:
        fs_home = settings.neuroflow_freesurfer_home.resolve()
        setup = fs_home / "SetUpFreeSurfer.sh"
        if setup.is_file():
            return ProbeResult(
                package_id="freesurfer",
                available=False,
                resolved_path=None,
                detail=f"FREESURFER_HOME configured ({fs_home}) but recon-all not executable",
            )

    return ProbeResult(
        package_id="freesurfer",
        available=False,
        detail=(
            "recon-all not found on PATH; "
            "set NEUROFLOW_RECON_ALL_BIN or NEUROFLOW_FREESURFER_HOME"
        ),
    )


def probe_fsl() -> ProbeResult:
    path = _first_on_path(("bet", "fsl", "flirt"))
    if path:
        return ProbeResult(
            package_id="fsl",
            available=True,
            resolved_path=path,
            detail="FSL binary found on PATH",
        )

    fsldir = _env_dir_exists(("FSLDIR",))
    if fsldir:
        return ProbeResult(
            package_id="fsl",
            available=True,
            resolved_path=fsldir,
            detail="FSLDIR points to an existing directory",
        )

    return ProbeResult(
        package_id="fsl",
        available=False,
        detail="No FSL binary on PATH and FSLDIR not set",
    )


def _slicer_executable_in_dir(dir_path: str) -> str | None:
    root = Path(dir_path)
    for name in ("Slicer", "slicer"):
        candidate = root / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def probe_slicer(settings: Settings) -> ProbeResult:
    resolved = resolve_executable(settings, "Slicer")
    if resolved is not None:
        return ProbeResult(
            package_id="slicer",
            available=True,
            resolved_path=str(resolved),
            detail="Slicer found",
        )

    path = _first_on_path(("Slicer", "slicer"))
    if path:
        return ProbeResult(
            package_id="slicer",
            available=True,
            resolved_path=path,
            detail="Slicer binary found on PATH",
        )

    if settings.neuroflow_slicer_home:
        found = _slicer_executable_in_dir(str(settings.neuroflow_slicer_home.resolve()))
        if found:
            return ProbeResult(
                package_id="slicer",
                available=True,
                resolved_path=found,
                detail="Slicer found under NEUROFLOW_SLICER_HOME",
            )

    for var in ("NEUROFLOW_SLICER_HOME", "SLICER_HOME"):
        value = os.environ.get(var)
        if value:
            found = _slicer_executable_in_dir(value)
            if found:
                return ProbeResult(
                    package_id="slicer",
                    available=True,
                    resolved_path=found,
                    detail=f"Slicer found under {var}",
                )

    return ProbeResult(
        package_id="slicer",
        available=False,
        detail="No Slicer binary on PATH; set NEUROFLOW_SLICER_HOME or SLICER_HOME",
    )


def probe_itk(settings: Settings) -> ProbeResult:
    configured, total = count_configured_native_binaries(settings)
    if configured > 0:
        first_path = None
        for module_id in (
            "itk-diffusion-complexity-mapping",
            "itk-anisotropic-anomalous-diffusion",
        ):
            resolved = resolve_itk_module_binary(settings, module_id)
            if resolved is not None:
                first_path = str(resolved)
                break
        return ProbeResult(
            package_id="itk",
            available=True,
            resolved_path=first_path,
            detail=f"{configured} of {total} native ITK module binary(ies) configured",
        )

    config_hint = "config/itk-binaries.json"
    if settings.neuroflow_itk_binaries_config:
        config_hint = str(settings.neuroflow_itk_binaries_config)
    return ProbeResult(
        package_id="itk",
        available=False,
        detail=(
            f"No native ITK binaries configured; copy config/itk-binaries.example.json "
            f"to {config_hint} and set absolute executable paths"
        ),
    )


def probe_ants(settings: Settings) -> ProbeResult:
    from neuroflow.tools.base import _ants_bin_dir, resolve_executable

    resolved = resolve_executable(settings, "antsRegistration")
    if resolved is not None:
        return ProbeResult(
            package_id="ants",
            available=True,
            resolved_path=str(resolved),
            detail="antsRegistration found",
        )

    path = _first_on_path(("antsRegistration", "ANTS", "antsApplyTransforms"))
    if path:
        return ProbeResult(
            package_id="ants",
            available=True,
            resolved_path=path,
            detail="ANTs binary found on PATH",
        )

    ants_bin = _ants_bin_dir(settings)
    if ants_bin is not None:
        candidate = ants_bin / "antsRegistration"
        if candidate.is_file():
            return ProbeResult(
                package_id="ants",
                available=False,
                resolved_path=None,
                detail=f"ANTSPATH configured ({ants_bin}) but antsRegistration not executable",
            )

    return ProbeResult(
        package_id="ants",
        available=False,
        detail="No ANTs binary on PATH; set NEUROFLOW_ANTSPATH or ANTSPATH",
    )


def _sct_bin_dir(settings: Settings) -> Path | None:
    if settings.neuroflow_sct_dir is not None:
        root = settings.neuroflow_sct_dir.resolve()
        if root.is_dir():
            return root
    for var in ("NEUROFLOW_SCT_DIR", "SCT_DIR"):
        value = os.environ.get(var)
        if value and Path(value).is_dir():
            return Path(value).resolve()
    return None


def _sct_executable_in_dir(dir_path: Path, name: str = "sct_version") -> str | None:
    for sub in ("bin", ""):
        candidate = dir_path / sub / name if sub else dir_path / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def probe_sct(settings: Settings) -> ProbeResult:
    path = _first_on_path(("sct_version", "sct_deepseg"))
    if path:
        return ProbeResult(
            package_id="sct",
            available=True,
            resolved_path=path,
            detail="SCT binary found on PATH",
        )

    sct_root = _sct_bin_dir(settings)
    if sct_root is not None:
        found = _sct_executable_in_dir(sct_root)
        if found:
            return ProbeResult(
                package_id="sct",
                available=True,
                resolved_path=found,
                detail="SCT found under SCT_DIR / NEUROFLOW_SCT_DIR",
            )
        return ProbeResult(
            package_id="sct",
            available=False,
            resolved_path=None,
            detail=f"SCT_DIR configured ({sct_root}) but sct_version not executable",
        )

    return ProbeResult(
        package_id="sct",
        available=False,
        detail="No SCT binary on PATH; set NEUROFLOW_SCT_DIR or SCT_DIR",
    )


_PROBE_FUNCTIONS = {
    "freesurfer": probe_freesurfer,
    "fsl": lambda settings: probe_fsl(),
    "ants": probe_ants,
    "slicer": probe_slicer,
    "itk": probe_itk,
    "sct": probe_sct,
}


def probe_package(settings: Settings, package_id: str) -> ProbeResult:
    probe_fn = _PROBE_FUNCTIONS.get(package_id)
    if probe_fn is None:
        return ProbeResult(
            package_id=package_id,
            available=False,
            detail="no probe configured",
        )
    return probe_fn(settings)


def scan_all_packages(settings: Settings) -> dict[str, ProbeResult]:
    """Run host probes for every registered package."""
    results: dict[str, ProbeResult] = {}
    for package_id in PACKAGE_IDS:
        results[package_id] = probe_package(settings, package_id)
    return results


def log_scan_summary(results: dict[str, ProbeResult]) -> None:
    logger.info("Host package scan")
    for package_id, result in sorted(results.items()):
        tool_name = _PACKAGE_DISPLAY_NAMES.get(package_id, package_id)
        if result.available:
            path = result.resolved_path or "ok"
            logger.info("Host probe %s: ready (%s)", tool_name, path)
        else:
            logger.info("Host probe %s: not ready — %s", tool_name, result.detail)


def package_available(results: dict[str, ProbeResult], package_id: str) -> bool:
    probe = results.get(package_id)
    return probe.available if probe else False


def module_available(
    results: dict[str, ProbeResult],
    module: ModuleDefinition,
    settings: Settings,
) -> bool:
    if module.required_executable:
        return which(module.required_executable) is not None or (
            module.required_executable == "eddy" and which("eddy_openmp") is not None
        )
    if module.availability_mode == "itk_binary":
        return resolve_itk_module_binary(settings, module.id) is not None
    if module.availability_mode == "worker_package":
        worker_id = module.worker_package_id or module.package_id
        return package_available(results, worker_id)
    return package_available(results, module.package_id)

"""BIDS-inspired dataset paths under NEUROFLOW_DATASETS_ROOT."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Literal

from neuroflow.config import Settings

Modality = Literal["anat", "dwi"]

_WORKSPACE_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_SUBJECT_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

# FSL modules that primarily operate on diffusion data.
_DWI_MODULE_IDS = frozenset(
    {
        "fsl-topup",
        "fsl-eddy",
        "fsl-dtifit",
        "fsl-bedpostx",
        "fsl-fdt",
        "fsl-probtrackx",
    }
)


def sanitize_workspace(name: str) -> str:
    cleaned = name.strip().replace(" ", "_")
    if not cleaned or not _WORKSPACE_RE.match(cleaned):
        raise ValueError(
            "Workspace must contain only letters, numbers, underscores, and hyphens"
        )
    return cleaned


def normalize_subject_id(subject_id: str) -> str:
    cleaned = subject_id.strip()
    if not cleaned or not _SUBJECT_RE.match(cleaned):
        raise ValueError(
            "Subject ID must contain only letters, numbers, underscores, and hyphens"
        )
    if not cleaned.lower().startswith("sub-"):
        cleaned = f"sub-{cleaned}"
    return cleaned


def modality_for_module(package_id: str, module_id: str) -> Modality:
    if package_id == "fsl" and module_id in _DWI_MODULE_IDS:
        return "dwi"
    return "anat"


def module_folder_name(module_id: str) -> str:
    """Short folder name under derivatives/<package>/ (e.g. fsl-bet -> bet)."""
    for prefix in ("fsl-", "freesurfer-", "ants-", "slicer-", "itk-"):
        if module_id.startswith(prefix):
            return module_id[len(prefix) :]
    return module_id


class DatasetStore:
    """Resolve and create BIDS-inspired workspace / subject trees."""

    def __init__(self, settings: Settings) -> None:
        self._root = settings.datasets_root
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def workspace_dir(self, workspace: str) -> Path:
        safe = sanitize_workspace(workspace)
        path = self._root / safe
        path.mkdir(parents=True, exist_ok=True)
        return path

    def subject_dir(self, workspace: str, subject_id: str) -> Path:
        sid = normalize_subject_id(subject_id)
        path = self.workspace_dir(workspace) / sid
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_subject_tree(
        self, workspace: str, subject_id: str, modality: Modality
    ) -> Path:
        modality_dir = self.subject_dir(workspace, subject_id) / modality
        modality_dir.mkdir(parents=True, exist_ok=True)
        return modality_dir

    def stage_input(
        self,
        *,
        workspace: str,
        subject_id: str,
        modality: Modality,
        source: Path,
        dest_name: str | None = None,
    ) -> Path:
        modality_dir = self.ensure_subject_tree(workspace, subject_id, modality)
        name = dest_name or source.name
        dest = modality_dir / name
        if source.resolve() != dest.resolve():
            shutil.copy2(source, dest)
        return dest

    def derivative_dir(self, workspace: str, package_id: str, module_id: str) -> Path:
        folder = module_folder_name(module_id)
        path = self.workspace_dir(workspace) / "derivatives" / package_id / folder
        path.mkdir(parents=True, exist_ok=True)
        return path

    def freesurfer_subjects_dir(self, workspace: str) -> Path:
        path = self.workspace_dir(workspace) / "derivatives" / "freesurfer"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def link_job_output_to_derivatives(self, job_output: Path, derivative: Path) -> None:
        """Replace job output dir with a symlink into the dataset derivatives tree."""
        derivative.mkdir(parents=True, exist_ok=True)
        if job_output.is_symlink() or job_output.exists():
            if job_output.is_dir() and not job_output.is_symlink():
                # Move any existing contents then replace with symlink.
                for child in job_output.iterdir():
                    target = derivative / child.name
                    if not target.exists():
                        shutil.move(str(child), str(target))
                shutil.rmtree(job_output)
            else:
                job_output.unlink()
        job_output.symlink_to(derivative.resolve())

"""MRIcron dcm2niix: one DICOM series to NIfTI with a fixed command."""

from __future__ import annotations

import shutil
import zipfile
from collections.abc import Callable
from pathlib import Path

from neuroflow.config import Settings
from neuroflow.services.datasets import DatasetStore, normalize_subject_id
from neuroflow.services.jobs import JobStore
from neuroflow.tools.base import resolve_executable, start_job_process

MRICRON_TOOL_ID = "mricron"
MODULE_ID = "mricron-dcm2niix"
FILENAME_PATTERN = "%n_%p_%s"


def build_argv(*, output_dir: Path, dicom_dir: Path) -> list[str]:
    """Fixed dcm2niix invocation. Filename is patient, protocol, then series."""
    return [
        "dcm2niix",
        "-z",
        "y",
        "-b",
        "y",
        "-ba",
        "y",
        "-f",
        FILENAME_PATTERN,
        "-o",
        str(output_dir),
        str(dicom_dir),
    ]


def ensure_dcm2niix_available(settings: Settings) -> Path:
    resolved = resolve_executable(settings, "dcm2niix")
    if resolved is None:
        raise FileNotFoundError(
            "dcm2niix was not found. Install it on PATH, place it in "
            "~/mricron or ~/MRIcron, or set NEUROFLOW_DCM2NIIX."
        )
    return resolved


def prepare_dicom_dir(saved_uploads: list[Path], dicom_dir: Path) -> None:
    """Collect one series into ``dicom_dir``.

    Accepts several ``.dcm`` files, or one ``.zip`` whose members are ``.dcm`` only.
    """
    dicom_dir.mkdir(parents=True, exist_ok=True)
    zips = [path for path in saved_uploads if path.suffix.lower() == ".zip"]
    others = [path for path in saved_uploads if path.suffix.lower() != ".zip"]

    if zips and others:
        raise ValueError("Upload either DICOM files or a single ZIP of one series, not both")
    if len(zips) > 1:
        raise ValueError("Upload one ZIP of a single DICOM series")
    if zips:
        _extract_dicom_zip(zips[0], dicom_dir)
        zips[0].unlink()
        return

    if not others:
        raise ValueError("At least one DICOM file is required")

    for path in others:
        if path.suffix.lower() != ".dcm":
            raise ValueError(f"Unsupported input for dcm2niix: {path.name}")
        dest = dicom_dir / path.name
        if dest.exists():
            raise ValueError(f"Duplicate DICOM filename: {path.name}")
        shutil.move(str(path), str(dest))


def _extract_dicom_zip(zip_path: Path, dest: Path) -> None:
    try:
        archive = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        raise ValueError("Upload is not a valid ZIP archive") from exc

    extracted = 0
    with archive:
        members = [info for info in archive.infolist() if not info.is_dir()]
        if not members:
            raise ValueError("ZIP archive contains no DICOM files")
        for info in members:
            raw = info.filename.replace("\\", "/")
            parts = Path(raw).parts
            if raw.startswith("/") or ".." in parts:
                raise ValueError("ZIP member path escapes the archive")
            name = Path(raw).name
            if not name or name.startswith("."):
                continue
            if not name.lower().endswith(".dcm"):
                raise ValueError(f"ZIP contains a non-DICOM member: {name}")
            target = dest / name
            if target.exists():
                raise ValueError(f"Duplicate DICOM filename: {name}")
            with archive.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
            extracted += 1

    if extracted == 0:
        raise ValueError("ZIP archive contains no DICOM files")


def copy_nifti_to_anat(
    settings: Settings,
    *,
    workspace: str,
    subject_id: str,
    derivative: Path,
) -> list[Path]:
    """Copy ``.nii.gz`` outputs into the subject ``anat/`` folder. JSON sidecars stay put."""
    datasets = DatasetStore(settings)
    anat = datasets.ensure_subject_tree(workspace, subject_id, "anat")
    copied: list[Path] = []
    for nii in sorted(derivative.glob("*.nii.gz")):
        target = anat / nii.name
        shutil.copy2(nii, target)
        copied.append(target)
    return copied


def launch_mricron_job(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    dicom_dir: Path,
    workspace: str,
    subject_id: str,
    copy_to_anat: bool,
) -> list[str]:
    """Link derivatives, then run the fixed dcm2niix command."""
    ensure_dcm2niix_available(settings)
    subject_id = normalize_subject_id(subject_id)
    datasets = DatasetStore(settings)
    job_dir = store.job_dir(MRICRON_TOOL_ID, job_id)
    derivative = datasets.derivative_dir(workspace, subject_id, MRICRON_TOOL_ID, MODULE_ID)
    datasets.link_job_output_to_derivatives(job_dir / "output", derivative)

    argv = build_argv(output_dir=derivative, dicom_dir=dicom_dir)
    dicom_names = sorted(path.name for path in dicom_dir.iterdir() if path.is_file())
    store.update_meta(
        MRICRON_TOOL_ID,
        job_id,
        command=argv,
        command_preview=" ".join(argv),
        workspace=workspace,
        subject_id=subject_id,
        dataset_output_dir=str(derivative),
        parameters={
            "module_id": MODULE_ID,
            "workspace": workspace,
            "subject_id": subject_id,
            "copy_to_anat": copy_to_anat,
            "filename_pattern": FILENAME_PATTERN,
        },
        input_files=dicom_names,
        estimated_total_seconds=int(0.05 * 3600),
    )

    def _on_complete(exit_code: int) -> None:
        if exit_code != 0 or not copy_to_anat:
            return
        try:
            copied = copy_nifti_to_anat(
                settings,
                workspace=workspace,
                subject_id=subject_id,
                derivative=derivative,
            )
        except OSError as exc:
            store.append_log(MRICRON_TOOL_ID, job_id, f"\nERROR copying NIfTI into anat/: {exc}\n")
            store.update_meta(
                MRICRON_TOOL_ID,
                job_id,
                status="failed",
                exit_code=1,
                error_message=str(exc),
            )
            return
        if copied:
            names = ", ".join(path.name for path in copied)
            store.append_log(MRICRON_TOOL_ID, job_id, f"\nCopied NIfTI into anat/: {names}\n")
        else:
            store.append_log(MRICRON_TOOL_ID, job_id, "\nNo NIfTI files to copy into anat/.\n")

    on_complete: Callable[[int], None] = _on_complete
    start_job_process(
        settings=settings,
        store=store,
        tool_id=MRICRON_TOOL_ID,
        job_id=job_id,
        argv=argv,
        cwd=job_dir,
        on_complete=on_complete,
    )
    return argv

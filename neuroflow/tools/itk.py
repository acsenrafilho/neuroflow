"""ITK / CSIM tool parameter mapping and job launcher (configured local binaries)."""

from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from neuroflow.config import Settings
from neuroflow.services.datasets import DatasetStore, modality_for_module, normalize_subject_id
from neuroflow.services.job_kill import is_job_cancelled, skip_if_cancelled
from neuroflow.services.jobs import JobStore
from neuroflow.tools.base import build_env, resolve_configured_binary
from neuroflow.tools.itk_binaries import resolve_itk_module_binary
from neuroflow.tools.registry import get_module

ITK_TOOL_ID = "itk"

VALID_MODULE_IDS = frozenset({"itk-diffusion-complexity-mapping"})

ROLE_INPUT = "input"
ROLE_MASK = "mask"

NIFTI_SUFFIXES = (".nii.gz", ".nii")

MODULE_REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "itk-diffusion-complexity-mapping": (ROLE_INPUT,),
}

_MODULE_BATCH_DRIVER: dict[str, str | None] = {
    "itk-diffusion-complexity-mapping": ROLE_INPUT,
}


class ItkJobParams(BaseModel):
    module_id: str
    output_prefix: str = Field(default="result", min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        if value not in VALID_MODULE_IDS:
            raise ValueError(f"Unknown ITK module: {value}")
        return value

    @field_validator("output_prefix")
    @classmethod
    def validate_output_prefix(cls, value: str) -> str:
        cleaned = value.strip()
        stem = strip_nifti_extension(cleaned)
        if not stem or not stem.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Output prefix must contain only letters, numbers, underscores, and hyphens "
                "(optional .nii or .nii.gz suffix is stripped automatically)"
            )
        return cleaned


def strip_nifti_extension(name: str) -> str:
    base = Path(name.strip()).name
    lower = base.lower()
    for suffix in NIFTI_SUFFIXES:
        if lower.endswith(suffix):
            return base[: -len(suffix)]
    return base


def infer_nifti_suffix(files: dict[str, Path]) -> str:
    for path in files.values():
        lower = path.name.lower()
        if lower.endswith(".nii.gz"):
            return ".nii.gz"
        if lower.endswith(".nii"):
            return ".nii"
    return ".nii.gz"


def subject_id_from_filename(filename: str) -> str:
    stem = strip_nifti_extension(filename)
    cleaned = stem.strip().replace(" ", "_")
    if cleaned and cleaned.replace("_", "").replace("-", "").isalnum():
        return cleaned[:64]
    return "run"


def required_roles(module_id: str) -> tuple[str, ...]:
    return MODULE_REQUIRED_ROLES.get(module_id, ())


def group_uploads_into_batch(
    module_id: str,
    files_by_role: dict[str, list[Path]],
) -> list[dict[str, Path]]:
    """Build one file-set per sequential ITK invocation (optional shared mask)."""
    needed = required_roles(module_id)
    if not needed:
        raise ValueError(f"Unknown module: {module_id}")

    missing = [role for role in needed if not files_by_role.get(role)]
    if missing:
        raise ValueError(f"Missing required file role(s): {', '.join(missing)}")

    driver = _MODULE_BATCH_DRIVER.get(module_id)
    if driver is None or driver not in needed:
        raise ValueError(f"Batch grouping not configured for module: {module_id}")

    driver_paths = files_by_role[driver]
    n = len(driver_paths)
    if n == 0:
        raise ValueError(f"No files uploaded for batch role: {driver}")

    mask_paths = files_by_role.get(ROLE_MASK, [])
    if mask_paths and len(mask_paths) not in (1, n):
        raise ValueError(
            f"Role '{ROLE_MASK}' has {len(mask_paths)} file(s); expected 1 shared or {n} "
            f"(one per batch item with '{driver}')"
        )

    items: list[dict[str, Path]] = []
    for index in range(n):
        item: dict[str, Path] = {driver: driver_paths[index]}
        if mask_paths:
            item[ROLE_MASK] = mask_paths[index] if len(mask_paths) == n else mask_paths[0]
        items.append(item)
    return items


def ensure_module_available(settings: Settings, module_id: str) -> Path:
    resolved = resolve_itk_module_binary(settings, module_id)
    if resolved is None:
        raise FileNotFoundError(
            f"ITK binary for {module_id} is not configured. "
            "Set paths in config/itk-binaries.json (see config/itk-binaries.example.json)."
        )
    return resolved


def build_argv(
    *,
    module_id: str,
    files: dict[str, Path],
    work_dir: Path,
    output_prefix: str,
    parameters: dict[str, Any],
    settings: Settings,
) -> list[str]:
    """Build argv for DiffusionComplexityMapping (argv[0] is absolute binary path)."""
    executable = ensure_module_available(settings, module_id)
    if module_id != "itk-diffusion-complexity-mapping":
        raise ValueError(f"Unsupported ITK module: {module_id}")

    input_path = files[ROLE_INPUT].resolve()
    out_dir = work_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = strip_nifti_extension(output_prefix)
    suffix = infer_nifti_suffix(files)
    output_path = (out_dir / f"{stem}{suffix}").resolve()

    q_value = parameters.get("q_value", 1.0)
    try:
        q_str = str(float(q_value))
    except (TypeError, ValueError) as exc:
        raise ValueError("q_value must be a number") from exc

    use_mask = bool(parameters.get("use_mask", True))
    mask_path = files.get(ROLE_MASK)
    if use_mask and mask_path is not None:
        return [
            str(executable),
            str(input_path),
            str(mask_path.resolve()),
            str(output_path),
            q_str,
        ]

    return [
        str(executable),
        str(input_path),
        str(output_path),
        q_str,
    ]


def output_prefix_for_batch(
    output_prefix: str,
    files: dict[str, Path],
    *,
    index: int,
    batch_total: int,
) -> str:
    if batch_total <= 1:
        return output_prefix
    stem = strip_nifti_extension(output_prefix)
    label = subject_id_from_filename(files[ROLE_INPUT].name)
    return f"{stem}_{label}"


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part


def _run_one_itk(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    argv: list[str],
    cwd: Path,
    scan_index: int,
    scan_total: int,
    label: str,
) -> int:
    executable = resolve_configured_binary(Path(argv[0]))
    if executable is None:
        raise FileNotFoundError(f"ITK executable not found or not executable: {argv[0]}")

    env = build_env(settings)
    cmd = [str(executable), *argv[1:]]
    preview = " ".join(_shell_quote(part) for part in cmd)

    store.append_log(
        ITK_TOOL_ID,
        job_id,
        f"\n=== Run {scan_index}/{scan_total}: {label} ===\n$ {preview}\n\n",
    )
    store.update_meta(
        ITK_TOOL_ID,
        job_id,
        batch_current_index=scan_index,
        command=cmd,
        command_preview=preview,
    )

    log_path = store.log_path(ITK_TOOL_ID, job_id)
    with log_path.open("a", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        store.update_meta(ITK_TOOL_ID, job_id, pid=proc.pid)
        if proc.stdout:
            for line in proc.stdout:
                log_file.write(line)
                log_file.flush()
        return proc.wait()


def launch_itk_job(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    module_id: str,
    batch_items: list[dict[str, Path]],
    output_prefix: str,
    parameters: dict[str, Any],
    workspace: str,
    subject_id: str,
) -> list[str]:
    if not batch_items:
        raise ValueError("At least one input set is required")

    ensure_module_available(settings, module_id)
    subject_id = normalize_subject_id(subject_id)
    datasets = DatasetStore(settings)
    modality = modality_for_module(ITK_TOOL_ID, module_id)
    for item_files in batch_items:
        for path in item_files.values():
            datasets.stage_input(
                workspace=workspace,
                subject_id=subject_id,
                modality=modality,
                source=path,
            )

    module_def = get_module(module_id)
    estimated_hours = module_def.estimated_hours_per_scan if module_def else 0.5
    batch_total = len(batch_items)
    estimated_total_seconds = int(batch_total * estimated_hours * 3600)

    job_dir = store.job_dir(ITK_TOOL_ID, job_id)
    derivative = datasets.derivative_dir(workspace, subject_id, ITK_TOOL_ID, module_id)
    datasets.link_job_output_to_derivatives(job_dir / "output", derivative)

    first_files = batch_items[0]
    first_prefix = output_prefix_for_batch(
        output_prefix,
        first_files,
        index=0,
        batch_total=batch_total,
    )
    first_argv = build_argv(
        module_id=module_id,
        files=first_files,
        work_dir=job_dir,
        output_prefix=first_prefix,
        parameters=parameters,
        settings=settings,
    )
    preview = " ".join(_shell_quote(part) for part in first_argv)
    if batch_total > 1:
        preview = f"{preview}  (+{batch_total - 1} more run(s) queued)"

    batch_meta = []
    for _index, files in enumerate(batch_items):
        batch_meta.append(
            {
                "filename": files[ROLE_INPUT].name,
                "subject_id": subject_id,
                "status": "pending",
            }
        )

    store.update_meta(
        ITK_TOOL_ID,
        job_id,
        status="running",
        workspace=workspace,
        subject_id=subject_id,
        dataset_output_dir=str(derivative),
        batch_items=batch_meta,
        batch_total=batch_total,
        batch_current_index=0,
        estimated_total_seconds=estimated_total_seconds,
        command_preview=preview,
        input_files=[str(p) for p in first_files.values()],
        parameters={
            "module_id": module_id,
            "workspace": workspace,
            "subject_id": subject_id,
            "output_prefix": output_prefix,
            **parameters,
        },
    )

    def _worker() -> None:
        try:
            for index, files in enumerate(batch_items, start=1):
                if skip_if_cancelled(store, ITK_TOOL_ID, job_id):
                    return

                prefix = output_prefix_for_batch(
                    output_prefix,
                    files,
                    index=index - 1,
                    batch_total=batch_total,
                )
                argv = build_argv(
                    module_id=module_id,
                    files=files,
                    work_dir=job_dir,
                    output_prefix=prefix,
                    parameters=parameters,
                    settings=settings,
                )
                label = subject_id
                batch_meta[index - 1]["status"] = "running"
                batch_meta[index - 1]["started_at"] = datetime.now(timezone.utc).isoformat()
                store.update_meta(ITK_TOOL_ID, job_id, batch_items=batch_meta)

                code = _run_one_itk(
                    settings=settings,
                    store=store,
                    job_id=job_id,
                    argv=argv,
                    cwd=job_dir,
                    scan_index=index,
                    scan_total=batch_total,
                    label=label,
                )
                finished = datetime.now(timezone.utc).isoformat()
                if skip_if_cancelled(store, ITK_TOOL_ID, job_id):
                    return
                if code != 0:
                    batch_meta[index - 1]["status"] = "failed"
                    batch_meta[index - 1]["finished_at"] = finished
                    batch_meta[index - 1]["error_message"] = f"Exit code {code}"
                    store.update_meta(
                        ITK_TOOL_ID,
                        job_id,
                        status="failed",
                        exit_code=code,
                        batch_items=batch_meta,
                        finished_at=finished,
                    )
                    return

                batch_meta[index - 1]["status"] = "completed"
                batch_meta[index - 1]["finished_at"] = finished
                store.update_meta(ITK_TOOL_ID, job_id, batch_items=batch_meta)

            if is_job_cancelled(store.read_meta(ITK_TOOL_ID, job_id)):
                return

            store.update_meta(
                ITK_TOOL_ID,
                job_id,
                status="completed",
                exit_code=0,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
        except (FileNotFoundError, ValueError, OSError) as exc:
            store.append_log(ITK_TOOL_ID, job_id, f"\nERROR: {exc}\n")
            store.update_meta(
                ITK_TOOL_ID,
                job_id,
                status="failed",
                exit_code=1,
                error_message=str(exc),
                finished_at=datetime.now(timezone.utc).isoformat(),
            )

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return [preview]

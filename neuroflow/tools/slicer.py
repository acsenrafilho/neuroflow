"""3D Slicer tool parameter mapping and job launcher (--launch CLI modules)."""

from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from neuroflow.config import Settings
from neuroflow.services.job_kill import is_job_cancelled, skip_if_cancelled
from neuroflow.services.jobs import JobStore
from neuroflow.tools.base import build_env, resolve_executable
from neuroflow.tools.registry import get_module

SLICER_TOOL_ID = "slicer"

VALID_MODULE_IDS = frozenset(
    {
        "slicer-dwi-convert",
        "slicer-dwi-mask",
        "slicer-dwi-to-dti",
    }
)

ROLE_INPUT = "input"
ROLE_BVALS = "bvals"
ROLE_BVECS = "bvecs"
ROLE_DWI = "dwi"
ROLE_BASELINE = "baseline"
ROLE_MASK = "mask"

NRRD_SUFFIX = ".nrrd"

MODULE_REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "slicer-dwi-convert": (ROLE_INPUT, ROLE_BVALS, ROLE_BVECS),
    "slicer-dwi-mask": (ROLE_DWI,),
    "slicer-dwi-to-dti": (ROLE_DWI, ROLE_BASELINE, ROLE_MASK),
}

_MODULE_BATCH_DRIVER: dict[str, str | None] = {
    "slicer-dwi-convert": ROLE_INPUT,
    "slicer-dwi-mask": ROLE_DWI,
    "slicer-dwi-to-dti": ROLE_DWI,
}


class SlicerJobParams(BaseModel):
    module_id: str
    output_prefix: str = Field(default="result", min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        if value not in VALID_MODULE_IDS:
            raise ValueError(f"Unknown 3D Slicer module: {value}")
        return value

    @field_validator("output_prefix")
    @classmethod
    def validate_output_prefix(cls, value: str) -> str:
        cleaned = value.strip()
        stem = strip_nrrd_extension(cleaned)
        if not stem or not stem.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Output prefix must contain only letters, numbers, underscores, and hyphens "
                "(optional .nrrd suffix is stripped automatically)"
            )
        return cleaned


def strip_nrrd_extension(name: str) -> str:
    """Return basename without .nrrd (case-insensitive)."""
    base = Path(name.strip()).name
    if base.lower().endswith(NRRD_SUFFIX):
        return base[: -len(NRRD_SUFFIX)]
    return base


def subject_id_from_filename(filename: str) -> str:
    stem = strip_nrrd_extension(filename)
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
    needed = required_roles(module_id)
    if not needed:
        raise ValueError(f"Unknown module: {module_id}")

    missing = [role for role in needed if not files_by_role.get(role)]
    if missing:
        raise ValueError(f"Missing required file role(s): {', '.join(missing)}")

    driver = _MODULE_BATCH_DRIVER.get(module_id)

    if driver is not None and driver in needed:
        driver_paths = files_by_role[driver]
        n = len(driver_paths)
        if n == 0:
            raise ValueError(f"No files uploaded for batch role: {driver}")

        for role in needed:
            if role == driver:
                continue
            count = len(files_by_role.get(role, []))
            if count not in (1, n):
                raise ValueError(
                    f"Role '{role}' has {count} file(s); expected 1 shared or {n} "
                    f"(one per batch item with '{driver}')"
                )

        items: list[dict[str, Path]] = []
        for index in range(n):
            item = {driver: driver_paths[index]}
            for role in needed:
                if role == driver:
                    continue
                paths = files_by_role[role]
                item[role] = paths[index] if len(paths) == n else paths[0]
            items.append(item)
        return items

    counts = {role: len(files_by_role[role]) for role in needed}
    unique = set(counts.values())
    if len(unique) != 1:
        raise ValueError(
            "For batch processing, each required role must have the same number of files "
            f"(got {dict(counts)})"
        )
    n = counts[needed[0]]
    if n < 1:
        raise ValueError("At least one file set is required")
    return [
        {role: files_by_role[role][index] for role in needed}
        for index in range(n)
    ]


def output_prefix_for_batch(
    base_prefix: str,
    files: dict[str, Path],
    module_id: str,
    *,
    index: int,
    batch_total: int,
) -> str:
    if batch_total <= 1:
        return base_prefix
    driver = _MODULE_BATCH_DRIVER.get(module_id)
    if driver and driver in files:
        stem = strip_nrrd_extension(files[driver].name)
        return f"{strip_nrrd_extension(base_prefix)}_{stem}"
    if batch_total > 1 and not driver:
        first_role = required_roles(module_id)[0]
        stem = strip_nrrd_extension(files[first_role].name)
        return f"{strip_nrrd_extension(base_prefix)}_{stem}"
    return f"{strip_nrrd_extension(base_prefix)}_{index + 1:03d}"


def output_path_kind(module_id: str) -> Literal["nrrd", "multi_nrrd"]:
    if module_id == "slicer-dwi-mask":
        return "multi_nrrd"
    return "nrrd"


def resolve_slicer_output_paths(
    module_id: str,
    out_dir: Path,
    output_prefix: str,
) -> list[Path]:
    base = strip_nrrd_extension(output_prefix)
    if module_id == "slicer-dwi-convert":
        return [out_dir / f"{base}{NRRD_SUFFIX}"]
    if module_id == "slicer-dwi-mask":
        return [
            out_dir / f"{base}_baseline{NRRD_SUFFIX}",
            out_dir / f"{base}_brain_mask{NRRD_SUFFIX}",
        ]
    if module_id == "slicer-dwi-to-dti":
        return [out_dir / f"{base}{NRRD_SUFFIX}"]
    return [out_dir / f"{base}{NRRD_SUFFIX}"]


def resolve_slicer_executable(settings: Settings) -> Path:
    executable = resolve_executable(settings, "Slicer")
    if executable is None:
        raise FileNotFoundError(
            "Slicer was not found on PATH. Install 3D Slicer or set "
            "NEUROFLOW_SLICER_HOME / SLICER_HOME."
        )
    return executable


def _flag(name: str, value: bool) -> list[str]:
    return [name] if value else []


def build_argv(
    *,
    module_id: str,
    files: dict[str, Path],
    work_dir: Path,
    output_prefix: str,
    parameters: dict[str, Any],
) -> list[str]:
    """Build argv starting with --launch (Slicer binary is prepended at run time)."""
    out_dir = work_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = strip_nrrd_extension(output_prefix)

    if module_id == "slicer-dwi-convert":
        argv = [
            "--launch",
            "DWIConvert",
            "--conversionMode",
            str(parameters.get("conversion_mode", "FSLToNrrd")),
            "--outputVolume",
            str((out_dir / f"{base}{NRRD_SUFFIX}").resolve()),
            "--fslNIFTIFile",
            str(files[ROLE_INPUT].resolve()),
            "--inputBValues",
            str(files[ROLE_BVALS].resolve()),
            "--inputBVectors",
            str(files[ROLE_BVECS].resolve()),
        ]
        if parameters.get("allow_lossy"):
            argv.append("--allowLossyConversion")
        return argv

    if module_id == "slicer-dwi-mask":
        argv = [
            "--launch",
            "DiffusionWeightedVolumeMasking",
        ]
        if parameters.get("remove_islands", True):
            argv.append("--removeislands")
        argv.extend(
            [
                str(files[ROLE_DWI].resolve()),
                str((out_dir / f"{base}_baseline{NRRD_SUFFIX}").resolve()),
                str((out_dir / f"{base}_brain_mask{NRRD_SUFFIX}").resolve()),
            ]
        )
        return argv

    if module_id == "slicer-dwi-to-dti":
        return [
            "--launch",
            "DWIToDTIEstimation",
            "--mask",
            str(files[ROLE_MASK].resolve()),
            "--enumeration",
            str(parameters.get("enumeration", "LS")),
            str(files[ROLE_DWI].resolve()),
            str((out_dir / f"{base}{NRRD_SUFFIX}").resolve()),
            str(files[ROLE_BASELINE].resolve()),
        ]

    raise ValueError(f"No argv builder for module: {module_id}")


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part


def _run_one_slicer(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    launch_argv: list[str],
    cwd: Path,
    scan_index: int,
    scan_total: int,
    label: str,
) -> int:
    slicer = resolve_slicer_executable(settings)
    env = build_env(settings)
    cmd = [str(slicer), *launch_argv]
    preview = " ".join(_shell_quote(part) for part in cmd)

    store.append_log(
        SLICER_TOOL_ID,
        job_id,
        f"\n=== Run {scan_index}/{scan_total}: {label} ===\n$ {preview}\n\n",
    )
    store.update_meta(
        SLICER_TOOL_ID,
        job_id,
        batch_current_index=scan_index,
        command=cmd,
        command_preview=preview,
    )

    log_path = store.log_path(SLICER_TOOL_ID, job_id)
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
        store.update_meta(SLICER_TOOL_ID, job_id, pid=proc.pid)
        if proc.stdout:
            for line in proc.stdout:
                log_file.write(line)
                log_file.flush()
        return proc.wait()


def launch_slicer_job(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    module_id: str,
    batch_items: list[dict[str, Path]],
    output_prefix: str,
    parameters: dict[str, Any],
) -> list[str]:
    """Run one or more Slicer --launch commands sequentially in a background job."""
    if not batch_items:
        raise ValueError("At least one input set is required")

    resolve_slicer_executable(settings)

    module_def = get_module(module_id)
    estimated_hours = module_def.estimated_hours_per_scan if module_def else 1.0
    batch_total = len(batch_items)
    estimated_total_seconds = int(batch_total * estimated_hours * 3600)

    job_dir = store.job_dir(SLICER_TOOL_ID, job_id)
    slicer = resolve_slicer_executable(settings)
    slicer_cwd = slicer.parent

    first_files = batch_items[0]
    first_prefix = output_prefix_for_batch(
        output_prefix,
        first_files,
        module_id,
        index=0,
        batch_total=batch_total,
    )
    first_argv = build_argv(
        module_id=module_id,
        files=first_files,
        work_dir=job_dir,
        output_prefix=first_prefix,
        parameters=parameters,
    )
    preview = " ".join(_shell_quote(part) for part in [str(slicer), *first_argv])
    if batch_total > 1:
        preview = f"{preview}  (+{batch_total - 1} more run(s) queued)"

    batch_meta = []
    for index, item_files in enumerate(batch_items):
        driver = _MODULE_BATCH_DRIVER.get(module_id)
        label_path = item_files.get(driver or required_roles(module_id)[0])
        filename = label_path.name if label_path else f"run-{index + 1}"
        batch_meta.append(
            {
                "filename": filename,
                "subject_id": subject_id_from_filename(filename),
                "status": "pending",
                "started_at": None,
                "finished_at": None,
                "error_message": None,
            }
        )

    all_input_names = [path.name for item in batch_items for path in item.values()]
    out_dir = job_dir / "output"
    store.update_meta(
        SLICER_TOOL_ID,
        job_id,
        command=[str(slicer), *first_argv],
        command_preview=preview,
        parameters={
            "module_id": module_id,
            "output_prefix": output_prefix,
            "resolved_outputs": [
                str(p) for p in resolve_slicer_output_paths(module_id, out_dir, first_prefix)
            ],
            "output_path_kind": output_path_kind(module_id),
            **parameters,
        },
        batch_items=batch_meta,
        batch_current_index=0,
        batch_total=batch_total,
        estimated_total_seconds=estimated_total_seconds,
        input_files=all_input_names,
        started_at=datetime.now(timezone.utc).isoformat(),
        status="running",
    )

    log_path = store.log_path(SLICER_TOOL_ID, job_id)
    log_path.write_text("", encoding="utf-8")

    def _run_batch() -> None:
        final_exit = 0
        try:
            for index, item_files in enumerate(batch_items, start=1):
                if skip_if_cancelled(store, SLICER_TOOL_ID, job_id):
                    return

                meta = store.read_meta(SLICER_TOOL_ID, job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    items[index - 1]["status"] = "running"
                    items[index - 1]["started_at"] = datetime.now(timezone.utc).isoformat()
                    store.update_meta(SLICER_TOOL_ID, job_id, batch_items=items)

                item_prefix = output_prefix_for_batch(
                    output_prefix,
                    item_files,
                    module_id,
                    index=index - 1,
                    batch_total=batch_total,
                )
                launch_argv = build_argv(
                    module_id=module_id,
                    files=item_files,
                    work_dir=job_dir,
                    output_prefix=item_prefix,
                    parameters=parameters,
                )
                driver = _MODULE_BATCH_DRIVER.get(module_id)
                label_path = item_files.get(driver or required_roles(module_id)[0])
                label = label_path.name if label_path else f"run-{index}"

                exit_code = _run_one_slicer(
                    settings=settings,
                    store=store,
                    job_id=job_id,
                    launch_argv=launch_argv,
                    cwd=slicer_cwd,
                    scan_index=index,
                    scan_total=batch_total,
                    label=label,
                )

                meta = store.read_meta(SLICER_TOOL_ID, job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    item_status = "completed" if exit_code == 0 else "failed"
                    items[index - 1]["status"] = item_status
                    items[index - 1]["finished_at"] = datetime.now(timezone.utc).isoformat()
                    if exit_code != 0:
                        items[index - 1]["error_message"] = (
                            f"Slicer exited with code {exit_code}"
                        )
                    store.update_meta(SLICER_TOOL_ID, job_id, batch_items=items)

                if skip_if_cancelled(store, SLICER_TOOL_ID, job_id):
                    return

                if exit_code != 0:
                    final_exit = exit_code
                    store.append_log(
                        SLICER_TOOL_ID,
                        job_id,
                        f"\nBatch stopped: run {index}/{batch_total} failed (exit {exit_code}).\n",
                    )
                    break
                final_exit = exit_code
        except OSError as exc:
            store.append_log(SLICER_TOOL_ID, job_id, f"\nERROR: {exc}\n")
            store.update_meta(
                SLICER_TOOL_ID,
                job_id,
                status="failed",
                exit_code=1,
                error_message=str(exc),
                finished_at=datetime.now(timezone.utc).isoformat(),
                pid=None,
            )
            return

        if is_job_cancelled(store.read_meta(SLICER_TOOL_ID, job_id)):
            return

        status = "completed" if final_exit == 0 else "failed"
        meta = store.read_meta(SLICER_TOOL_ID, job_id)
        store.update_meta(
            SLICER_TOOL_ID,
            job_id,
            status=status,
            exit_code=final_exit,
            finished_at=datetime.now(timezone.utc).isoformat(),
            pid=None,
            batch_current_index=(
                batch_total if status == "completed" else int(meta.get("batch_current_index") or 0)
            ),
        )

    thread = threading.Thread(target=_run_batch, daemon=True)
    thread.start()
    return [str(slicer), *first_argv]

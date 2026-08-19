"""Spinal Cord Toolbox (SCT) parameter mapping and job launcher."""

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
from neuroflow.tools.base import build_env, resolve_executable
from neuroflow.tools.registry import get_module

SCT_TOOL_ID = "sct"

VALID_MODULE_IDS = frozenset(
    {
        "sct-deepseg",
        "sct-propseg",
        "sct-get-centerline",
        "sct-create-mask",
        "sct-label-vertebrae",
        "sct-register-to-template",
        "sct-warp-template",
        "sct-apply-transfo",
        "sct-process-segmentation",
        "sct-qc",
    }
)

SCT_QC_PROCESSES = frozenset({"sct_deepseg_sc", "sct_label_vertebrae"})

ROLE_INPUT = "input"
ROLE_SEG = "seg"
ROLE_CENTERLINE = "centerline"
ROLE_LABELS = "labels"
ROLE_DEST = "dest"
ROLE_WARP = "warp"
ROLE_VERTFILE = "vertfile"

NIFTI_SUFFIXES: tuple[str, ...] = (".nii.gz", ".nii")

MODULE_REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "sct-deepseg": (ROLE_INPUT,),
    "sct-propseg": (ROLE_INPUT,),
    "sct-get-centerline": (ROLE_INPUT,),
    "sct-create-mask": (ROLE_INPUT,),
    "sct-label-vertebrae": (ROLE_INPUT, ROLE_SEG),
    "sct-register-to-template": (ROLE_INPUT, ROLE_SEG),
    "sct-warp-template": (ROLE_DEST, ROLE_WARP),
    "sct-apply-transfo": (ROLE_INPUT, ROLE_DEST, ROLE_WARP),
    "sct-process-segmentation": (ROLE_INPUT,),
    "sct-qc": (ROLE_INPUT, ROLE_SEG),
}

# Optional roles accepted when uploaded (not required for grouping).
MODULE_OPTIONAL_ROLES: dict[str, tuple[str, ...]] = {
    "sct-create-mask": (ROLE_CENTERLINE,),
    "sct-register-to-template": (ROLE_LABELS,),
    "sct-process-segmentation": (ROLE_VERTFILE,),
}

_MODULE_BATCH_DRIVER: dict[str, str | None] = {
    "sct-deepseg": ROLE_INPUT,
    "sct-propseg": ROLE_INPUT,
    "sct-get-centerline": ROLE_INPUT,
    "sct-create-mask": ROLE_INPUT,
    "sct-label-vertebrae": ROLE_INPUT,
    "sct-register-to-template": ROLE_INPUT,
    "sct-warp-template": ROLE_DEST,
    "sct-apply-transfo": ROLE_INPUT,
    "sct-process-segmentation": ROLE_INPUT,
    "sct-qc": ROLE_INPUT,
}

MODULE_PRIMARY_EXECUTABLE: dict[str, str] = {
    "sct-deepseg": "sct_deepseg",
    "sct-propseg": "sct_propseg",
    "sct-get-centerline": "sct_get_centerline",
    "sct-create-mask": "sct_create_mask",
    "sct-label-vertebrae": "sct_label_vertebrae",
    "sct-register-to-template": "sct_register_to_template",
    "sct-warp-template": "sct_warp_template",
    "sct-apply-transfo": "sct_apply_transfo",
    "sct-process-segmentation": "sct_process_segmentation",
    "sct-qc": "sct_qc",
}


class SctJobParams(BaseModel):
    module_id: str
    output_prefix: str = Field(default="result", min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        if value not in VALID_MODULE_IDS:
            raise ValueError(f"Unknown SCT module: {value}")
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


def required_roles(module_id: str) -> tuple[str, ...]:
    return MODULE_REQUIRED_ROLES.get(module_id, ())


def group_uploads_into_batch(
    module_id: str,
    files_by_role: dict[str, list[Path]],
) -> list[dict[str, Path]]:
    """Build one file-set per sequential SCT invocation (FSL-style batching)."""
    needed = list(required_roles(module_id))
    if not needed:
        raise ValueError(f"Unknown module: {module_id}")

    optional = MODULE_OPTIONAL_ROLES.get(module_id, ())
    for role in optional:
        if files_by_role.get(role):
            needed.append(role)

    missing = [role for role in required_roles(module_id) if not files_by_role.get(role)]
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
    return [{role: files_by_role[role][index] for role in needed} for index in range(n)]


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
        stem = strip_nifti_extension(files[driver].name)
        return f"{strip_nifti_extension(base_prefix)}_{stem}"
    first_role = required_roles(module_id)[0]
    stem = strip_nifti_extension(files[first_role].name)
    return f"{strip_nifti_extension(base_prefix)}_{stem}"


def _opt_flag(name: str, value: Any) -> list[str]:
    if value is None or value == "":
        return []
    return [name, str(value)]


def _flag_enabled(value: Any) -> bool:
    """True when an SCT 0/1 flag is explicitly on."""
    if value is None or value == "":
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    try:
        return int(value) == 1
    except (TypeError, ValueError):
        return False


def build_argv(
    *,
    module_id: str,
    files: dict[str, Path],
    work_dir: Path,
    output_prefix: str,
    parameters: dict[str, Any],
) -> list[str]:
    """Build argv for a single SCT command. Paths must be absolute."""
    out_dir = work_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = strip_nifti_extension(output_prefix)
    suffix = infer_nifti_suffix(files)

    if module_id == "sct-deepseg":
        task = str(parameters.get("task") or "spinalcord")
        out_path = out_dir / f"{base}_seg{suffix}"
        return [
            "sct_deepseg",
            task,
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            str(out_path),
        ]

    if module_id == "sct-propseg":
        contrast = str(parameters.get("contrast") or "t2")
        return [
            "sct_propseg",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-c",
            contrast,
            "-ofolder",
            str(out_dir),
        ]

    if module_id == "sct-get-centerline":
        out_path = out_dir / f"{base}_centerline{suffix}"
        argv = [
            "sct_get_centerline",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            str(out_path),
        ]
        method = parameters.get("method")
        if method:
            argv.extend(["-method", str(method)])
        contrast = parameters.get("contrast")
        if contrast:
            argv.extend(["-c", str(contrast)])
        return argv

    if module_id == "sct-create-mask":
        process = str(parameters.get("process") or "center")
        if process == "centerline":
            if ROLE_CENTERLINE not in files:
                raise ValueError("Role 'centerline' is required when process mode is 'centerline'")
            process_arg = f"centerline,{files[ROLE_CENTERLINE].resolve()}"
        else:
            process_arg = "center"
        out_path = out_dir / f"{base}_mask{suffix}"
        argv = [
            "sct_create_mask",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-p",
            process_arg,
            "-o",
            str(out_path),
        ]
        shape = parameters.get("shape")
        if shape:
            argv.extend(["-f", str(shape)])
        size = parameters.get("size")
        if size:
            argv.extend(["-size", str(size)])
        return argv

    if module_id == "sct-label-vertebrae":
        contrast = str(parameters.get("contrast") or "t2")
        return [
            "sct_label_vertebrae",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-s",
            str(files[ROLE_SEG].resolve()),
            "-c",
            contrast,
            "-ofolder",
            str(out_dir),
        ]

    if module_id == "sct-register-to-template":
        contrast = str(parameters.get("contrast") or "t2")
        argv = [
            "sct_register_to_template",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-s",
            str(files[ROLE_SEG].resolve()),
            "-c",
            contrast,
            "-ofolder",
            str(out_dir),
        ]
        if ROLE_LABELS in files:
            argv.extend(["-l", str(files[ROLE_LABELS].resolve())])
        return argv

    if module_id == "sct-warp-template":
        return [
            "sct_warp_template",
            "-d",
            str(files[ROLE_DEST].resolve()),
            "-w",
            str(files[ROLE_WARP].resolve()),
            "-ofolder",
            str(out_dir),
        ]

    if module_id == "sct-apply-transfo":
        out_path = out_dir / f"{base}_warped{suffix}"
        argv = [
            "sct_apply_transfo",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-d",
            str(files[ROLE_DEST].resolve()),
            "-w",
            str(files[ROLE_WARP].resolve()),
            "-o",
            str(out_path),
        ]
        interp = parameters.get("interpolation")
        if interp:
            argv.extend(["-x", str(interp)])
        return argv

    if module_id == "sct-process-segmentation":
        out_path = out_dir / f"{base}_csa.csv"
        argv = [
            "sct_process_segmentation",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            str(out_path),
        ]
        vert = str(parameters.get("vert") or "").strip()
        perlevel = parameters.get("perlevel")
        needs_vertfile = bool(vert) or _flag_enabled(perlevel)
        if needs_vertfile and ROLE_VERTFILE not in files:
            raise ValueError("Role 'vertfile' is required when -vert or -perlevel is set")
        if ROLE_VERTFILE in files:
            argv.extend(["-vertfile", str(files[ROLE_VERTFILE].resolve())])
        if vert:
            argv.extend(["-vert", vert])
        if perlevel is not None and perlevel != "":
            argv.extend(["-perlevel", str(int(perlevel))])
        perslice = parameters.get("perslice")
        if perslice is not None and perslice != "":
            argv.extend(["-perslice", str(int(perslice))])
        angle_corr = parameters.get("angle_corr")
        if angle_corr is None:
            angle_corr = parameters.get("angle-corr")
        if angle_corr is not None and angle_corr != "":
            argv.extend(["-angle-corr", str(int(angle_corr))])
        return argv

    if module_id == "sct-qc":
        process = str(parameters.get("process") or "sct_deepseg_sc")
        if process not in SCT_QC_PROCESSES:
            allowed = ", ".join(sorted(SCT_QC_PROCESSES))
            raise ValueError(f"Unsupported sct_qc process '{process}'. Allowed: {allowed}")
        qc_dir = out_dir / "qc"
        argv = [
            "sct_qc",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-p",
            process,
            "-s",
            str(files[ROLE_SEG].resolve()),
            "-qc",
            str(qc_dir),
        ]
        return argv

    raise ValueError(f"No argv builder for module: {module_id}")


def ensure_module_available(
    settings: Settings, module_id: str, parameters: dict[str, Any] | None = None
) -> str:
    """Return executable name for module; raise if missing."""
    del parameters  # unused; kept for FSL-compatible signature
    executable = MODULE_PRIMARY_EXECUTABLE[module_id]
    if resolve_executable(settings, executable) is None:
        raise FileNotFoundError(
            f"{executable} was not found on PATH. Install SCT or set SCT_DIR / NEUROFLOW_SCT_DIR."
        )
    return executable


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part


def _run_one_sct(
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
    executable = resolve_executable(settings, argv[0])
    if executable is None:
        raise FileNotFoundError(f"Executable not found on PATH: {argv[0]}")

    env = build_env(settings)
    cmd = [str(executable), *argv[1:]]
    preview = " ".join(_shell_quote(part) for part in cmd)

    store.append_log(
        SCT_TOOL_ID,
        job_id,
        f"\n=== Run {scan_index}/{scan_total}: {label} ===\n$ {preview}\n\n",
    )
    store.update_meta(
        SCT_TOOL_ID,
        job_id,
        batch_current_index=scan_index,
        command=cmd,
        command_preview=preview,
    )

    log_path = store.log_path(SCT_TOOL_ID, job_id)
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
        store.update_meta(SCT_TOOL_ID, job_id, pid=proc.pid)
        if proc.stdout:
            for line in proc.stdout:
                log_file.write(line)
                log_file.flush()
        return proc.wait()


def launch_sct_job(
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
    """Run one or more SCT commands sequentially in a background job."""
    if not batch_items:
        raise ValueError("At least one input set is required")

    ensure_module_available(settings, module_id, parameters)
    subject_id = normalize_subject_id(subject_id)
    datasets = DatasetStore(settings)
    modality = modality_for_module(SCT_TOOL_ID, module_id)
    for item_files in batch_items:
        for path in item_files.values():
            datasets.stage_input(
                workspace=workspace,
                subject_id=subject_id,
                modality=modality,
                source=path,
            )

    module_def = get_module(module_id)
    estimated_hours = module_def.estimated_hours_per_scan if module_def else 1.0
    batch_total = len(batch_items)
    estimated_total_seconds = int(batch_total * estimated_hours * 3600)

    job_dir = store.job_dir(SCT_TOOL_ID, job_id)
    derivative = datasets.derivative_dir(workspace, subject_id, SCT_TOOL_ID, module_id)
    datasets.link_job_output_to_derivatives(job_dir / "output", derivative)

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
    preview = " ".join(_shell_quote(part) for part in first_argv)
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
                "subject_id": subject_id,
                "status": "pending",
                "started_at": None,
                "finished_at": None,
                "error_message": None,
            }
        )

    all_input_names = [path.name for item in batch_items for path in item.values()]
    store.update_meta(
        SCT_TOOL_ID,
        job_id,
        command=first_argv,
        command_preview=preview,
        workspace=workspace,
        subject_id=subject_id,
        dataset_output_dir=str(derivative),
        parameters={
            "module_id": module_id,
            "workspace": workspace,
            "subject_id": subject_id,
            "output_prefix": output_prefix,
            **parameters,
        },
        batch_items=batch_meta,
        batch_current_index=0,
        batch_total=batch_total,
        estimated_total_seconds=estimated_total_seconds,
        input_files=all_input_names,
        started_at=datetime.now(timezone.utc).isoformat(),
        status="running",
        queue_reason=None,
    )

    log_path = store.log_path(SCT_TOOL_ID, job_id)
    log_path.write_text("", encoding="utf-8")

    def _run_batch() -> None:
        final_exit = 0
        try:
            for index, item_files in enumerate(batch_items, start=1):
                if skip_if_cancelled(store, SCT_TOOL_ID, job_id):
                    return

                meta = store.read_meta(SCT_TOOL_ID, job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    items[index - 1]["status"] = "running"
                    items[index - 1]["started_at"] = datetime.now(timezone.utc).isoformat()
                    store.update_meta(SCT_TOOL_ID, job_id, batch_items=items)

                item_prefix = output_prefix_for_batch(
                    output_prefix,
                    item_files,
                    module_id,
                    index=index - 1,
                    batch_total=batch_total,
                )
                argv = build_argv(
                    module_id=module_id,
                    files=item_files,
                    work_dir=job_dir,
                    output_prefix=item_prefix,
                    parameters=parameters,
                )
                driver = _MODULE_BATCH_DRIVER.get(module_id)
                label_path = item_files.get(driver or required_roles(module_id)[0])
                label = label_path.name if label_path else f"run-{index}"

                exit_code = _run_one_sct(
                    settings=settings,
                    store=store,
                    job_id=job_id,
                    argv=argv,
                    cwd=job_dir,
                    scan_index=index,
                    scan_total=batch_total,
                    label=label,
                )

                meta = store.read_meta(SCT_TOOL_ID, job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    item_status = "completed" if exit_code == 0 else "failed"
                    items[index - 1]["status"] = item_status
                    items[index - 1]["finished_at"] = datetime.now(timezone.utc).isoformat()
                    if exit_code != 0:
                        items[index - 1]["error_message"] = f"SCT exited with code {exit_code}"
                    store.update_meta(SCT_TOOL_ID, job_id, batch_items=items)

                if skip_if_cancelled(store, SCT_TOOL_ID, job_id):
                    return

                if exit_code != 0:
                    final_exit = exit_code
                    store.append_log(
                        SCT_TOOL_ID,
                        job_id,
                        f"\nBatch stopped: run {index}/{batch_total} failed (exit {exit_code}).\n",
                    )
                    break
                final_exit = exit_code
        except OSError as exc:
            store.append_log(SCT_TOOL_ID, job_id, f"\nERROR: {exc}\n")
            store.update_meta(
                SCT_TOOL_ID,
                job_id,
                status="failed",
                exit_code=1,
                error_message=str(exc),
                finished_at=datetime.now(timezone.utc).isoformat(),
                pid=None,
            )
            return

        if is_job_cancelled(store.read_meta(SCT_TOOL_ID, job_id)):
            return

        status = "completed" if final_exit == 0 else "failed"
        meta = store.read_meta(SCT_TOOL_ID, job_id)
        store.update_meta(
            SCT_TOOL_ID,
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
    return first_argv

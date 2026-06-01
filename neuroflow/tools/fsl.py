"""FSL tool parameter mapping and job launcher."""

from __future__ import annotations

import shutil
import subprocess
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from neuroflow.config import Settings
from neuroflow.services.jobs import JobStore
from neuroflow.tools.base import build_env, resolve_executable
from neuroflow.tools.registry import get_module

FSL_TOOL_ID = "fsl"

VALID_MODULE_IDS = frozenset(
    {
        "fsl-bet",
        "fsl-fast",
        "fsl-first",
        "fsl-bianca",
        "fsl-siena",
        "fsl-eddy",
        "fsl-topup",
        "fsl-fdt",
        "fsl-bedpostx",
        "fsl-tbss",
        "fsl-flirt",
        "fsl-fnirt",
        "fsl-susan",
        "fsl-epi-reg",
        "fsl-mcflirt",
    }
)

ROLE_INPUT = "input"
ROLE_REFERENCE = "reference"
ROLE_MOVING = "moving"
ROLE_MASK = "mask"
ROLE_AFFINE = "affine_mat"
ROLE_BVALS = "bvals"
ROLE_BVECS = "bvecs"
ROLE_ACQP = "acqp"
ROLE_INDEX = "index"
ROLE_EPI = "epi"
ROLE_T1 = "t1"
ROLE_T1_BRAIN = "t1_brain"
ROLE_TIME1 = "time1"
ROLE_TIME2 = "time2"
ROLE_FA = "fa"
ROLE_SUBJECT_DIR = "subject_dir"
ROLE_FEATURE_FILE = "feature_file"

NIFTI_SUFFIXES: tuple[str, ...] = (".nii.gz", ".nii")

# FSL adds its own suffixes (e.g. BET → _brain.nii.gz); do not pass an image extension.
_PREFIX_OUTPUT_MODULES = frozenset(
    {
        "fsl-bet",
        "fsl-fast",
        "fsl-mcflirt",
        "fsl-topup",
        "fsl-eddy",
        "fsl-fdt",
        "fsl-epi-reg",
        "fsl-bianca",
    }
)

# Output argument must be a full image path ending in .nii or .nii.gz.
_IMAGE_OUTPUT_MODULES = frozenset(
    {
        "fsl-susan",
        "fsl-flirt",
        "fsl-fnirt",
    }
)

MODULE_REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "fsl-bet": (ROLE_INPUT,),
    "fsl-fast": (ROLE_INPUT,),
    "fsl-susan": (ROLE_INPUT,),
    "fsl-mcflirt": (ROLE_INPUT,),
    "fsl-flirt": (ROLE_MOVING, ROLE_REFERENCE),
    "fsl-fnirt": (ROLE_MOVING, ROLE_REFERENCE, ROLE_AFFINE),
    "fsl-first": (ROLE_INPUT,),
    "fsl-epi-reg": (ROLE_EPI, ROLE_T1, ROLE_T1_BRAIN),
    "fsl-siena": (ROLE_TIME1, ROLE_TIME2),
    "fsl-topup": (ROLE_INPUT, ROLE_ACQP),
    "fsl-eddy": (
        ROLE_INPUT,
        ROLE_MASK,
        ROLE_INDEX,
        ROLE_ACQP,
        ROLE_BVECS,
        ROLE_BVALS,
    ),
    "fsl-fdt": (ROLE_INPUT, ROLE_BVECS, ROLE_BVALS),
    "fsl-bedpostx": (ROLE_SUBJECT_DIR,),
    "fsl-tbss": (ROLE_FA,),
    "fsl-bianca": (ROLE_FEATURE_FILE,),
}

# Role that may repeat across uploads; other required roles use 1 (shared) or N (paired).
_MODULE_BATCH_DRIVER: dict[str, str | None] = {
    "fsl-bet": ROLE_INPUT,
    "fsl-fast": ROLE_INPUT,
    "fsl-susan": ROLE_INPUT,
    "fsl-mcflirt": ROLE_INPUT,
    "fsl-first": ROLE_INPUT,
    "fsl-tbss": ROLE_FA,
    "fsl-bedpostx": ROLE_SUBJECT_DIR,
    "fsl-bianca": ROLE_FEATURE_FILE,
    "fsl-epi-reg": ROLE_EPI,
    "fsl-topup": ROLE_INPUT,
    "fsl-fdt": ROLE_INPUT,
    "fsl-fnirt": ROLE_MOVING,
    "fsl-flirt": None,
    "fsl-siena": None,
    "fsl-eddy": ROLE_INPUT,
}

_MODULE_INPUT_ROLE_PRIORITY: dict[str, tuple[str, ...]] = {
    "fsl-bet": (ROLE_INPUT,),
    "fsl-fast": (ROLE_INPUT,),
    "fsl-susan": (ROLE_INPUT,),
    "fsl-mcflirt": (ROLE_INPUT,),
    "fsl-flirt": (ROLE_MOVING, ROLE_REFERENCE),
    "fsl-fnirt": (ROLE_MOVING, ROLE_REFERENCE),
    "fsl-first": (ROLE_INPUT,),
    "fsl-epi-reg": (ROLE_EPI, ROLE_T1, ROLE_T1_BRAIN),
    "fsl-topup": (ROLE_INPUT,),
    "fsl-eddy": (ROLE_INPUT,),
    "fsl-fdt": (ROLE_INPUT, ROLE_MASK),
    "fsl-tbss": (ROLE_FA,),
}


class FslJobParams(BaseModel):
    module_id: str
    output_prefix: str = Field(default="result", min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        if value not in VALID_MODULE_IDS:
            raise ValueError(f"Unknown FSL module: {value}")
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


def subject_id_from_filename(filename: str) -> str:
    """Derive a safe batch label from an input filename (for BatchItemStatus)."""
    stem = strip_nifti_extension(filename)
    cleaned = stem.strip().replace(" ", "_")
    if cleaned and cleaned.replace("_", "").replace("-", "").isalnum():
        return cleaned[:64]
    return "run"


def strip_nifti_extension(name: str) -> str:
    """Return basename without .nii or .nii.gz (case-insensitive)."""
    base = Path(name.strip()).name
    lower = base.lower()
    for suffix in NIFTI_SUFFIXES:
        if lower.endswith(suffix):
            return base[: -len(suffix)]
    return base


def infer_nifti_suffix(
    files: dict[str, Path],
    *,
    role_priority: tuple[str, ...] = (),
) -> str:
    """Pick .nii.gz or .nii from uploaded inputs; default .nii.gz."""
    roles = role_priority or tuple(files.keys())
    for role in roles:
        path = files.get(role)
        if path is None:
            continue
        lower = path.name.lower()
        if lower.endswith(".nii.gz"):
            return ".nii.gz"
        if lower.endswith(".nii"):
            return ".nii"
    for path in files.values():
        lower = path.name.lower()
        if lower.endswith(".nii.gz"):
            return ".nii.gz"
        if lower.endswith(".nii"):
            return ".nii"
    return ".nii.gz"


def resolve_fsl_output_path(
    module_id: str,
    out_dir: Path,
    output_prefix: str,
    files: dict[str, Path],
) -> Path:
    """
    Resolve the path passed to FSL for -o / --out / output arguments.

    - prefix: basename only (FSL appends _brain, _seg, etc.)
    - image: full path with .nii or .nii.gz matching inputs
    - directory: output folder (FIRST)
    """
    base = strip_nifti_extension(output_prefix)
    priority = _MODULE_INPUT_ROLE_PRIORITY.get(module_id, ())
    suffix = infer_nifti_suffix(files, role_priority=priority)

    if module_id == "fsl-first":
        path = out_dir / base
        path.mkdir(parents=True, exist_ok=True)
        return path

    if module_id in _IMAGE_OUTPUT_MODULES:
        return out_dir / f"{base}{suffix}"

    if module_id in _PREFIX_OUTPUT_MODULES:
        return out_dir / base

    return out_dir / base


def required_roles(module_id: str) -> tuple[str, ...]:
    return MODULE_REQUIRED_ROLES.get(module_id, ())


def group_uploads_into_batch(
    module_id: str,
    files_by_role: dict[str, list[Path]],
) -> list[dict[str, Path]]:
    """
    Build one file-set per sequential FSL invocation.

    - With a batch driver role: N driver files → N runs; other roles are shared (1 file)
      or paired (N files, one per run).
    - Without a driver: every required role must have 1 or the same N files (zipped).
    """
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
    """Unique output prefix per batch item when running multiple inputs."""
    if batch_total <= 1:
        return base_prefix
    driver = _MODULE_BATCH_DRIVER.get(module_id)
    if driver and driver in files:
        stem = strip_nifti_extension(files[driver].name)
        return f"{strip_nifti_extension(base_prefix)}_{stem}"
    if batch_total > 1 and not driver:
        first_role = required_roles(module_id)[0]
        stem = strip_nifti_extension(files[first_role].name)
        return f"{strip_nifti_extension(base_prefix)}_{stem}"
    return f"{strip_nifti_extension(base_prefix)}_{index + 1:03d}"


def output_path_kind(module_id: str) -> Literal["prefix", "image", "directory", "none"]:
    if module_id == "fsl-first":
        return "directory"
    if module_id in {"fsl-siena", "fsl-bedpostx", "fsl-tbss"}:
        return "none"
    if module_id in _IMAGE_OUTPUT_MODULES:
        return "image"
    if module_id in _PREFIX_OUTPUT_MODULES:
        return "prefix"
    return "prefix"


def _flag(name: str, value: bool) -> list[str]:
    return [name] if value else []


def _opt_flag(name: str, value: Any) -> list[str]:
    if value is None or value == "":
        return []
    return [name, str(value)]


def _resolve_eddy_executable(settings: Settings) -> str:
    if resolve_executable(settings, "eddy_openmp") is not None:
        return "eddy_openmp"
    return "eddy"


def build_argv(
    *,
    module_id: str,
    files: dict[str, Path],
    work_dir: Path,
    output_prefix: str,
    parameters: dict[str, Any],
    settings: Settings,
) -> list[str]:
    """Build argv for a single FSL command. Paths must be absolute."""
    out_dir = work_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = resolve_fsl_output_path(module_id, out_dir, output_prefix, files)
    base_stem = strip_nifti_extension(output_prefix)

    if module_id == "fsl-bet":
        executable = "bet2" if parameters.get("bet_mode") == "bet2" else "bet"
        argv: list[str] = [executable, str(files[ROLE_INPUT].resolve()), str(prefix)]
        argv.extend(_opt_flag("-f", parameters.get("fractional_intensity")))
        argv.extend(_opt_flag("-g", parameters.get("vertical_gradient")))
        if parameters.get("generate_mask"):
            argv.append("-m")
        if parameters.get("robust"):
            argv.append("-R")
        if parameters.get("remove_neck"):
            argv.append("-n")
        return argv

    if module_id == "fsl-fast":
        tissue = parameters.get("tissue_type", 1)
        segments = parameters.get("n_segments", 3)
        return [
            "fast",
            "-t",
            str(tissue),
            "-n",
            str(segments),
            "-o",
            str(prefix),
            str(files[ROLE_INPUT].resolve()),
        ]

    if module_id == "fsl-susan":
        return [
            "susan",
            str(files[ROLE_INPUT].resolve()),
            str(prefix),
            str(parameters.get("effective_sigma", 3.0)),
            str(parameters.get("mixture_value", 0.0)),
        ]

    if module_id == "fsl-mcflirt":
        argv = [
            "mcflirt",
            "-in",
            str(files[ROLE_INPUT].resolve()),
            "-out",
            str(prefix),
        ]
        if parameters.get("generate_plots"):
            argv.append("-plots")
        cost = parameters.get("cost")
        if cost:
            argv.extend(["-cost", str(cost)])
        motion_model = parameters.get("motion_model")
        if motion_model:
            argv.extend(["-m", str(motion_model)])
        return argv

    if module_id == "fsl-flirt":
        argv = [
            "flirt",
            "-in",
            str(files[ROLE_MOVING].resolve()),
            "-ref",
            str(files[ROLE_REFERENCE].resolve()),
            "-out",
            str(prefix),
        ]
        argv.extend(_opt_flag("-dof", parameters.get("dof", 6)))
        argv.extend(_opt_flag("-cost", parameters.get("cost", "corratio")))
        if parameters.get("save_matrix", True):
            argv.extend(["-omat", str(out_dir / f"{base_stem}.mat")])
        if ROLE_MASK in files:
            argv.extend(["-refweight", str(files[ROLE_MASK].resolve())])
        return argv

    if module_id == "fsl-fnirt":
        argv = [
            "fnirt",
            f"--in={files[ROLE_MOVING].resolve()}",
            f"--ref={files[ROLE_REFERENCE].resolve()}",
            f"--aff={files[ROLE_AFFINE].resolve()}",
            f"--iout={prefix}",
        ]
        if parameters.get("config_file"):
            argv.append(f"--config={parameters['config_file']}")
        return argv

    if module_id == "fsl-first":
        return [
            "run_first_all",
            "-i",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            str(prefix),
        ]

    if module_id == "fsl-epi_reg":
        argv = [
            "epi_reg",
            f"--epi={files[ROLE_EPI].resolve()}",
            f"--t1={files[ROLE_T1].resolve()}",
            f"--t1brain={files[ROLE_T1_BRAIN].resolve()}",
            f"--out={prefix}",
        ]
        argv.extend(_opt_flag("--dof", parameters.get("dof", 6)))
        return argv

    if module_id == "fsl-siena":
        return [
            "siena",
            str(files[ROLE_TIME1].resolve()),
            str(files[ROLE_TIME2].resolve()),
        ]

    if module_id == "fsl-topup":
        argv = [
            "topup",
            f"--imain={files[ROLE_INPUT].resolve()}",
            f"--datain={files[ROLE_ACQP].resolve()}",
            f"--out={prefix}",
        ]
        if parameters.get("readout"):
            argv.append(f"--readout={parameters['readout']}")
        return argv

    if module_id == "fsl-eddy":
        eddy_bin = _resolve_eddy_executable(settings)
        argv = [
            eddy_bin,
            f"--imain={files[ROLE_INPUT].resolve()}",
            f"--mask={files[ROLE_MASK].resolve()}",
            f"--index={files[ROLE_INDEX].resolve()}",
            f"--acqp={files[ROLE_ACQP].resolve()}",
            f"--bvecs={files[ROLE_BVECS].resolve()}",
            f"--bvals={files[ROLE_BVALS].resolve()}",
            f"--out={prefix}",
        ]
        n_threads = parameters.get("n_threads")
        if n_threads:
            argv.append(f"--nthr={n_threads}")
        return argv

    if module_id == "fsl-fdt":
        argv = [
            "dtifit",
            "-k",
            str(files[ROLE_INPUT].resolve()),
            "-o",
            str(prefix),
            "-r",
            str(files[ROLE_BVECS].resolve()),
            "-b",
            str(files[ROLE_BVALS].resolve()),
        ]
        if ROLE_MASK in files:
            argv.extend(["-m", str(files[ROLE_MASK].resolve())])
        return argv

    if module_id == "fsl-bedpostx":
        subject_dir = _prepare_bedpostx_dir(files[ROLE_SUBJECT_DIR], work_dir)
        n_fibres = int(parameters.get("n_fibres", 2))
        return ["bedpostx", str(subject_dir), str(n_fibres)]

    if module_id == "fsl-tbss":
        fa_dest = out_dir / Path(files[ROLE_FA].name)
        if not fa_dest.exists():
            shutil.copy2(files[ROLE_FA], fa_dest)
        return ["tbss_1_preproc", str(fa_dest)]

    if module_id == "fsl-bianca":
        argv = [
            "bianca",
            f"-featurefile={files[ROLE_FEATURE_FILE].resolve()}",
            f"-o={prefix}",
        ]
        if parameters.get("training_mask"):
            argv.append(f"-training_mask={parameters['training_mask']}")
        return argv

    raise ValueError(f"No argv builder for module: {module_id}")


def _prepare_bedpostx_dir(upload_path: Path, work_dir: Path) -> Path:
    """Unpack zip subject directory or use existing folder layout."""
    dest = work_dir / "bedpostx_subject"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    if upload_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(upload_path, "r") as archive:
            archive.extractall(dest)
        children = list(dest.iterdir())
        if len(children) == 1 and children[0].is_dir():
            return children[0]
        return dest

    shutil.copy2(upload_path, dest / upload_path.name)
    return dest


MODULE_PRIMARY_EXECUTABLE: dict[str, str] = {
    "fsl-bet": "bet",
    "fsl-fast": "fast",
    "fsl-susan": "susan",
    "fsl-mcflirt": "mcflirt",
    "fsl-flirt": "flirt",
    "fsl-fnirt": "fnirt",
    "fsl-first": "run_first_all",
    "fsl-epi-reg": "epi_reg",
    "fsl-siena": "siena",
    "fsl-topup": "topup",
    "fsl-eddy": "eddy",
    "fsl-fdt": "dtifit",
    "fsl-bedpostx": "bedpostx",
    "fsl-tbss": "tbss_1_preproc",
    "fsl-bianca": "bianca",
}


def primary_executable(module_id: str, settings: Settings, parameters: dict[str, Any]) -> str:
    if (
        module_id == "fsl-bet"
        and parameters.get("bet_mode") == "bet2"
        and resolve_executable(settings, "bet2") is not None
    ):
        return "bet2"
    if module_id == "fsl-eddy":
        return _resolve_eddy_executable(settings)
    return MODULE_PRIMARY_EXECUTABLE[module_id]


def ensure_module_available(
    settings: Settings, module_id: str, parameters: dict[str, Any] | None = None
) -> str:
    """Return executable name for module; raise if missing."""
    params = parameters or {}
    executable = primary_executable(module_id, settings, params)
    if resolve_executable(settings, executable) is None:
        raise FileNotFoundError(
            f"{executable} was not found on PATH. Install FSL or set FSLDIR / NEUROFLOW_FSLDIR."
        )
    return executable


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part


def _run_one_fsl(
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
        FSL_TOOL_ID,
        job_id,
        f"\n=== Run {scan_index}/{scan_total}: {label} ===\n$ {preview}\n\n",
    )
    store.update_meta(
        FSL_TOOL_ID,
        job_id,
        batch_current_index=scan_index,
        command=cmd,
        command_preview=preview,
    )

    log_path = store.log_path(FSL_TOOL_ID, job_id)
    with log_path.open("a", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        store.update_meta(FSL_TOOL_ID, job_id, pid=proc.pid)
        if proc.stdout:
            for line in proc.stdout:
                log_file.write(line)
                log_file.flush()
        return proc.wait()


def launch_fsl_job(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    module_id: str,
    batch_items: list[dict[str, Path]],
    output_prefix: str,
    parameters: dict[str, Any],
) -> list[str]:
    """Run one or more FSL commands sequentially in a background job."""
    if not batch_items:
        raise ValueError("At least one input set is required")

    ensure_module_available(settings, module_id, parameters)

    module_def = get_module(module_id)
    estimated_hours = module_def.estimated_hours_per_scan if module_def else 1.0
    batch_total = len(batch_items)
    estimated_total_seconds = int(batch_total * estimated_hours * 3600)

    job_dir = store.job_dir(FSL_TOOL_ID, job_id)
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
        settings=settings,
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
                "subject_id": subject_id_from_filename(filename),
                "status": "pending",
                "started_at": None,
                "finished_at": None,
                "error_message": None,
            }
        )

    all_input_names = [
        path.name for item in batch_items for path in item.values()
    ]
    store.update_meta(
        FSL_TOOL_ID,
        job_id,
        command=first_argv,
        command_preview=preview,
        parameters={
            "module_id": module_id,
            "output_prefix": output_prefix,
            "resolved_output": str(
                resolve_fsl_output_path(
                    module_id,
                    job_dir / "output",
                    first_prefix,
                    first_files,
                )
            ),
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

    log_path = store.log_path(FSL_TOOL_ID, job_id)
    log_path.write_text("", encoding="utf-8")

    def _run_batch() -> None:
        final_exit = 0
        try:
            for index, item_files in enumerate(batch_items, start=1):
                meta = store.read_meta(FSL_TOOL_ID, job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    items[index - 1]["status"] = "running"
                    items[index - 1]["started_at"] = datetime.now(timezone.utc).isoformat()
                    store.update_meta(FSL_TOOL_ID, job_id, batch_items=items)

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
                    settings=settings,
                )
                driver = _MODULE_BATCH_DRIVER.get(module_id)
                label_path = item_files.get(driver or required_roles(module_id)[0])
                label = label_path.name if label_path else f"run-{index}"

                exit_code = _run_one_fsl(
                    settings=settings,
                    store=store,
                    job_id=job_id,
                    argv=argv,
                    cwd=job_dir,
                    scan_index=index,
                    scan_total=batch_total,
                    label=label,
                )

                meta = store.read_meta(FSL_TOOL_ID, job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    item_status = "completed" if exit_code == 0 else "failed"
                    items[index - 1]["status"] = item_status
                    items[index - 1]["finished_at"] = datetime.now(timezone.utc).isoformat()
                    if exit_code != 0:
                        items[index - 1]["error_message"] = (
                            f"FSL exited with code {exit_code}"
                        )
                    store.update_meta(FSL_TOOL_ID, job_id, batch_items=items)

                if exit_code != 0:
                    final_exit = exit_code
                    store.append_log(
                        FSL_TOOL_ID,
                        job_id,
                        f"\nBatch stopped: run {index}/{batch_total} failed (exit {exit_code}).\n",
                    )
                    break
                final_exit = exit_code
        except OSError as exc:
            store.append_log(FSL_TOOL_ID, job_id, f"\nERROR: {exc}\n")
            store.update_meta(
                FSL_TOOL_ID,
                job_id,
                status="failed",
                exit_code=1,
                error_message=str(exc),
                finished_at=datetime.now(timezone.utc).isoformat(),
                pid=None,
            )
            return

        status = "completed" if final_exit == 0 else "failed"
        meta = store.read_meta(FSL_TOOL_ID, job_id)
        store.update_meta(
            FSL_TOOL_ID,
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

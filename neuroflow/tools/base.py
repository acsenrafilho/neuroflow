"""Safe subprocess execution for allowlisted binaries."""

from __future__ import annotations

import os
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path
from shutil import which

from neuroflow.config import Settings
from neuroflow.services.job_kill import is_job_cancelled, skip_if_cancelled
from neuroflow.services.jobs import JobStore

ALLOWLISTED_EXECUTABLES = frozenset(
    {
        "recon-all",
        "bet",
        "bet2",
        "fast",
        "susan",
        "mcflirt",
        "flirt",
        "fnirt",
        "run_first_all",
        "epi_reg",
        "siena",
        "topup",
        "eddy",
        "eddy_openmp",
        "dtifit",
        "bedpostx",
        "tbss_1_preproc",
        "bianca",
        "Slicer",
        "antsRegistration",
        "antsApplyTransforms",
        "N4BiasFieldCorrection",
        "Atropos",
        "ImageMath",
        "sccan",
        "KellyKapowski",
        "antsMotionCorr",
        "DenoiseImage",
        "antsTransformInfo",
        "CreateJacobianDeterminantImage",
        "ResampleImage",
        "ThresholdImage",
        "SmoothImage",
        "ConvertImage",
        "MeasureImageSimilarity",
        "antsJointFusion",
        "antsRegistrationSyN.sh",
        "antsRegistrationSyNQuick.sh",
        "antsCorticalThickness.sh",
        "antsBrainExtraction.sh",
        "antsMultivariateTemplateConstruction2.sh",
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
    }
)


def _ants_bin_dir(settings: Settings) -> Path | None:
    if settings.neuroflow_antspath is not None:
        root = settings.neuroflow_antspath.resolve()
        if root.is_dir():
            return root
    for var in ("NEUROFLOW_ANTSPATH", "ANTSPATH"):
        value = os.environ.get(var)
        if not value:
            continue
        root = Path(value.rstrip("/"))
        if root.is_dir():
            return root
        parent = root.parent
        if parent.is_dir() and (parent / "antsRegistration").is_file():
            return parent
    return None


def _apply_antspath_env(env: dict[str, str], bin_dir: Path) -> None:
    antspath = str(bin_dir.resolve())
    if not antspath.endswith(os.sep):
        antspath += os.sep
    env["ANTSPATH"] = antspath
    env["PATH"] = f"{bin_dir.resolve()}{os.pathsep}{env.get('PATH', '')}"


def _sct_root_dir(settings: Settings) -> Path | None:
    if settings.neuroflow_sct_dir is not None:
        root = settings.neuroflow_sct_dir.resolve()
        if root.is_dir():
            return root
    for var in ("NEUROFLOW_SCT_DIR", "SCT_DIR"):
        value = os.environ.get(var)
        if value and Path(value).is_dir():
            return Path(value).resolve()
    return None


def resolve_executable(settings: Settings, name: str) -> Path | None:
    if name not in ALLOWLISTED_EXECUTABLES:
        return None

    if name == "recon-all" and settings.neuroflow_recon_all_bin:
        candidate = settings.neuroflow_recon_all_bin
        if os.path.isabs(candidate) and os.access(candidate, os.X_OK):
            return Path(candidate)
        found = which(candidate)
        if found:
            return Path(found)

    if settings.neuroflow_fsldir:
        fsldir = settings.neuroflow_fsldir.resolve()
        for sub in ("bin", ""):
            candidate = fsldir / sub / name if sub else fsldir / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate

    if name == "Slicer":
        if settings.neuroflow_slicer_home:
            home = settings.neuroflow_slicer_home.resolve()
            for slicer_name in ("Slicer", "slicer"):
                candidate = home / slicer_name
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return candidate
        for slicer_name in ("Slicer", "slicer"):
            found = which(slicer_name)
            if found:
                return Path(found)

    ants_bin = _ants_bin_dir(settings)
    if ants_bin is not None:
        candidate = ants_bin / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    sct_root = _sct_root_dir(settings)
    if sct_root is not None:
        for sub in ("bin", ""):
            candidate = sct_root / sub / name if sub else sct_root / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate

    found = which(name)
    return Path(found) if found else None


def resolve_configured_binary(path: Path) -> Path | None:
    """Validate an absolute path from ITK binaries config (no allowlist name required)."""
    resolved = path.resolve()
    if resolved.is_file() and os.access(resolved, os.X_OK):
        return resolved
    return None


def resolve_job_executable(settings: Settings, argv0: str) -> Path | None:
    """Resolve argv[0] from ITK config path or allowlisted PATH name."""
    candidate = Path(argv0)
    if candidate.is_absolute():
        return resolve_configured_binary(candidate)
    return resolve_executable(settings, argv0)


def build_env(settings: Settings) -> dict[str, str]:
    env = os.environ.copy()
    if settings.neuroflow_freesurfer_home:
        fs_home = str(settings.neuroflow_freesurfer_home.resolve())
        env["FREESURFER_HOME"] = fs_home
        setup = Path(fs_home) / "SetUpFreeSurfer.sh"
        if setup.is_file():
            env["NEUROFLOW_FREESURFER_SETUP"] = str(setup)

    if settings.neuroflow_fsldir:
        fsldir = str(settings.neuroflow_fsldir.resolve())
        env["FSLDIR"] = fsldir
        fs_bin = Path(fsldir) / "bin"
        if fs_bin.is_dir():
            env["PATH"] = f"{fs_bin}{os.pathsep}{env.get('PATH', '')}"

    slicer_home = settings.neuroflow_slicer_home
    if slicer_home is None:
        for var in ("NEUROFLOW_SLICER_HOME", "SLICER_HOME"):
            value = os.environ.get(var)
            if value and Path(value).is_dir():
                slicer_home = Path(value)
                break
    if slicer_home is not None:
        home = str(slicer_home.resolve())
        env["SLICER_HOME"] = home
        env["PATH"] = f"{home}{os.pathsep}{env.get('PATH', '')}"

    ants_bin = _ants_bin_dir(settings)
    if ants_bin is not None:
        _apply_antspath_env(env, ants_bin)

    sct_root = _sct_root_dir(settings)
    if sct_root is not None:
        env["SCT_DIR"] = str(sct_root)
        sct_bin = sct_root / "bin"
        if sct_bin.is_dir():
            env["PATH"] = f"{sct_bin}{os.pathsep}{env.get('PATH', '')}"
        else:
            env["PATH"] = f"{sct_root}{os.pathsep}{env.get('PATH', '')}"

    return env


def start_job_process(
    *,
    settings: Settings,
    store: JobStore,
    tool_id: str,
    job_id: str,
    argv: list[str],
    cwd: Path,
    subjects_dir: Path | None = None,
    on_complete: Callable[[int], None] | None = None,
) -> int:
    """Start allowlisted process in background; stream output to run.log."""
    executable = resolve_job_executable(settings, argv[0])
    if executable is None:
        raise FileNotFoundError(f"Executable not found: {argv[0]}")

    env = build_env(settings)
    if subjects_dir is not None:
        env["SUBJECTS_DIR"] = str(subjects_dir.resolve())

    log_path = store.log_path(tool_id, job_id)
    log_path.write_text("", encoding="utf-8")

    cmd = [str(executable), *argv[1:]]
    store.update_meta(
        tool_id,
        job_id,
        status="running",
        command=cmd,
        command_preview=" ".join(_shell_quote(part) for part in cmd),
        started_at=_utc_now(),
    )
    store.append_log(tool_id, job_id, f"$ {' '.join(_shell_quote(part) for part in cmd)}\n\n")

    def _run() -> None:
        exit_code = 1
        try:
            if skip_if_cancelled(store, tool_id, job_id):
                return
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
                store.update_meta(tool_id, job_id, pid=proc.pid)
                if proc.stdout:
                    for line in proc.stdout:
                        log_file.write(line)
                        log_file.flush()
                exit_code = proc.wait()
        except OSError as exc:
            store.append_log(tool_id, job_id, f"\nERROR: {exc}\n")
            store.update_meta(
                tool_id,
                job_id,
                status="failed",
                exit_code=exit_code,
                error_message=str(exc),
            )
            if on_complete:
                on_complete(exit_code)
            return

        if is_job_cancelled(store.read_meta(tool_id, job_id)):
            return

        status = "completed" if exit_code == 0 else "failed"
        store.update_meta(
            tool_id,
            job_id,
            status=status,
            exit_code=exit_code,
            finished_at=_utc_now(),
        )
        if on_complete:
            on_complete(exit_code)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return 0


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part

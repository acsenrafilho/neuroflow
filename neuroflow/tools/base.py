"""Safe subprocess execution for allowlisted binaries."""

from __future__ import annotations

import os
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path
from shutil import which

from neuroflow.config import Settings
from neuroflow.services.jobs import JobStore

ALLOWLISTED_EXECUTABLES = frozenset({"recon-all"})


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
    found = which(name)
    return Path(found) if found else None


def build_env(settings: Settings) -> dict[str, str]:
    env = os.environ.copy()
    if settings.neuroflow_freesurfer_home:
        fs_home = str(settings.neuroflow_freesurfer_home.resolve())
        env["FREESURFER_HOME"] = fs_home
        setup = Path(fs_home) / "SetUpFreeSurfer.sh"
        if setup.is_file():
            env["NEUROFLOW_FREESURFER_SETUP"] = str(setup)
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
    executable_name = argv[0]
    executable = resolve_executable(settings, executable_name)
    if executable is None:
        raise FileNotFoundError(f"Executable not found on PATH: {executable_name}")

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
    )
    store.append_log(tool_id, job_id, f"$ {' '.join(_shell_quote(part) for part in cmd)}\n\n")

    def _run() -> None:
        exit_code = 1
        try:
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

        status = "completed" if exit_code == 0 else "failed"
        from datetime import datetime, timezone

        store.update_meta(
            tool_id,
            job_id,
            status=status,
            exit_code=exit_code,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        if on_complete:
            on_complete(exit_code)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return 0


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part

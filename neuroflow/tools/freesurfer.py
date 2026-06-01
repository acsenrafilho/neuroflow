"""FreeSurfer recon-all parameter mapping and job launcher."""

from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from neuroflow.config import Settings
from neuroflow.services.jobs import JobStore
from neuroflow.tools.base import build_env, resolve_executable
from neuroflow.tools.registry import ReconOption

RECON_FLAGS: dict[ReconOption, str] = {
    "all": "-all",
    "autorecon1": "-autorecon1",
    "autorecon2": "-autorecon2",
    "autorecon3": "-autorecon3",
}


class FreeSurferJobParams(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=64)
    recon_options: ReconOption = "all"

    @field_validator("subject_id")
    @classmethod
    def validate_subject_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Subject ID must contain only letters, numbers, underscores, and hyphens"
            )
        return cleaned


class BatchScan(BaseModel):
    subject_id: str
    input_path: Path


def build_recon_all_argv(
    *,
    subject_id: str,
    input_path: Path,
    recon_options: ReconOption,
) -> list[str]:
    argv = [
        "recon-all",
        "-s",
        subject_id,
        "-i",
        str(input_path.resolve()),
        RECON_FLAGS[recon_options],
    ]
    return argv


def ensure_recon_all_available(settings: Settings) -> None:
    if resolve_executable(settings, "recon-all") is None:
        raise FileNotFoundError(
            "recon-all was not found on PATH. Install FreeSurfer or set NEUROFLOW_RECON_ALL_BIN."
        )


def _shell_quote(part: str) -> str:
    if not part or any(c in part for c in " \t\n\"'$\\"):
        return '"' + part.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return part


def _run_one_recon(
    *,
    settings: Settings,
    store: JobStore,
    tool_id: str,
    job_id: str,
    argv: list[str],
    cwd: Path,
    subjects_dir: Path,
    scan_index: int,
    scan_total: int,
    subject_id: str,
) -> int:
    executable = resolve_executable(settings, argv[0])
    if executable is None:
        raise FileNotFoundError(f"Executable not found on PATH: {argv[0]}")

    env = build_env(settings)
    env["SUBJECTS_DIR"] = str(subjects_dir.resolve())
    cmd = [str(executable), *argv[1:]]
    preview = " ".join(_shell_quote(part) for part in cmd)

    store.append_log(
        tool_id,
        job_id,
        f"\n=== Scan {scan_index}/{scan_total}: {subject_id} ===\n$ {preview}\n\n",
    )
    store.update_meta(
        tool_id,
        job_id,
        batch_current_index=scan_index,
        command=cmd,
        command_preview=preview,
    )

    log_path = store.log_path(tool_id, job_id)
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
        return proc.wait()


def launch_freesurfer_job(
    *,
    settings: Settings,
    store: JobStore,
    job_id: str,
    recon_options: ReconOption,
    scans: list[BatchScan],
    estimated_hours_per_scan: float,
) -> list[str]:
    """Run one or more recon-all scans sequentially in a single background job."""
    ensure_recon_all_available(settings)
    if not scans:
        raise ValueError("At least one scan is required")

    job_dir = store.job_dir("freesurfer", job_id)
    subjects_dir = job_dir / "output"
    batch_total = len(scans)
    estimated_total_seconds = int(batch_total * estimated_hours_per_scan * 3600)

    batch_items = [
        {
            "filename": scan.input_path.name,
            "subject_id": scan.subject_id,
            "status": "pending",
            "started_at": None,
            "finished_at": None,
            "error_message": None,
        }
        for scan in scans
    ]

    first_argv = build_recon_all_argv(
        subject_id=scans[0].subject_id,
        input_path=scans[0].input_path,
        recon_options=recon_options,
    )
    preview = " ".join(_shell_quote(part) for part in first_argv)
    if batch_total > 1:
        preview = f"{preview}  (+{batch_total - 1} more scan(s) queued)"

    store.update_meta(
        "freesurfer",
        job_id,
        command=first_argv,
        command_preview=preview,
        parameters={
            "recon_options": recon_options,
            "batch_subject_ids": [s.subject_id for s in scans],
        },
        batch_items=batch_items,
        batch_current_index=0,
        batch_total=batch_total,
        estimated_total_seconds=estimated_total_seconds,
        started_at=datetime.now(timezone.utc).isoformat(),
        status="running",
        input_files=[s.input_path.name for s in scans],
    )

    log_path = store.log_path("freesurfer", job_id)
    log_path.write_text("", encoding="utf-8")

    def _run_batch() -> None:
        final_exit = 0
        try:
            for index, scan in enumerate(scans, start=1):
                meta = store.read_meta("freesurfer", job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    items[index - 1]["status"] = "running"
                    items[index - 1]["started_at"] = datetime.now(timezone.utc).isoformat()
                    store.update_meta("freesurfer", job_id, batch_items=items)

                argv = build_recon_all_argv(
                    subject_id=scan.subject_id,
                    input_path=scan.input_path,
                    recon_options=recon_options,
                )
                exit_code = _run_one_recon(
                    settings=settings,
                    store=store,
                    tool_id="freesurfer",
                    job_id=job_id,
                    argv=argv,
                    cwd=job_dir,
                    subjects_dir=subjects_dir,
                    scan_index=index,
                    scan_total=batch_total,
                    subject_id=scan.subject_id,
                )

                meta = store.read_meta("freesurfer", job_id)
                items = meta.get("batch_items") or []
                if index - 1 < len(items):
                    item_status = "completed" if exit_code == 0 else "failed"
                    items[index - 1]["status"] = item_status
                    items[index - 1]["finished_at"] = datetime.now(timezone.utc).isoformat()
                    if exit_code != 0:
                        items[index - 1]["error_message"] = (
                            f"recon-all exited with code {exit_code}"
                        )
                    store.update_meta("freesurfer", job_id, batch_items=items)

                if exit_code != 0:
                    final_exit = exit_code
                    store.append_log(
                        "freesurfer",
                        job_id,
                        f"\nBatch stopped: scan {index}/{batch_total} failed (exit {exit_code}).\n",
                    )
                    break
                final_exit = exit_code
        except OSError as exc:
            store.append_log("freesurfer", job_id, f"\nERROR: {exc}\n")
            store.update_meta(
                "freesurfer",
                job_id,
                status="failed",
                exit_code=1,
                error_message=str(exc),
                finished_at=datetime.now(timezone.utc).isoformat(),
                pid=None,
            )
            return

        status = "completed" if final_exit == 0 else "failed"
        meta = store.read_meta("freesurfer", job_id)
        store.update_meta(
            "freesurfer",
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

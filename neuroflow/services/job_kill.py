"""Cancel running jobs by terminating their subprocess tree."""

from __future__ import annotations

import os
import signal
import time
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

from neuroflow.services.jobs import JobStore


class JobKillError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def is_job_cancelled(meta: dict[str, Any]) -> bool:
    return bool(meta.get("cancel_requested")) or meta.get("status") == "cancelled"


def skip_if_cancelled(store: JobStore, tool_id: str, job_id: str) -> bool:
    return is_job_cancelled(store.read_meta(tool_id, job_id))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _terminate_process_tree(pid: int, grace_seconds: float = 2.0) -> None:
    try:
        pgid = os.getpgid(pid)
    except ProcessLookupError:
        return

    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            return

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)

    with suppress(ProcessLookupError, PermissionError):
        os.killpg(pgid, signal.SIGKILL)
    with suppress(ProcessLookupError, PermissionError):
        os.kill(pid, signal.SIGKILL)


def request_job_kill(store: JobStore, tool_id: str, job_id: str) -> dict[str, Any]:
    try:
        meta = store.read_meta(tool_id, job_id)
    except FileNotFoundError as exc:
        raise JobKillError(
            "job_not_found",
            f"Job not found: {job_id}",
            404,
        ) from exc

    status = meta.get("status")
    if status not in ("queued", "running"):
        raise JobKillError(
            "job_not_killable",
            f"Job is already {status}",
            409,
        )

    store.update_meta(tool_id, job_id, cancel_requested=True)

    pid = meta.get("pid")
    if pid:
        _terminate_process_tree(int(pid))

    meta = store.read_meta(tool_id, job_id)
    if meta.get("status") == "cancelled":
        return meta

    store.append_log(tool_id, job_id, "\nJob stopped by user.\n")
    store.update_meta(
        tool_id,
        job_id,
        status="cancelled",
        error_message="Stopped by user",
        exit_code=-1,
        finished_at=_utc_now(),
        pid=None,
    )
    return store.read_meta(tool_id, job_id)

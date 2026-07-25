"""Mark orphaned running/queued jobs after API restart."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from neuroflow.services.job_list import list_jobs
from neuroflow.services.jobs import JobStore

logger = logging.getLogger(__name__)

_RUNNING_MSG = "Orphaned after server restart (process no longer running)"
_QUEUED_MSG = "Cleared after server restart (in-memory queue was not resumed)"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pid_alive(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        pid_i = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_i <= 0:
        return False
    try:
        os.kill(pid_i, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we cannot signal it — treat as still alive.
        return True
    except OSError:
        return False
    return True


def reconcile_orphaned_jobs(store: JobStore) -> dict[str, int]:
    """
    After a cold start, fix jobs left as running/queued on disk.

    - running without a live PID → failed
    - queued (starters are in-process only) → cancelled

    Returns counts of jobs updated per new status.
    """
    updated = {"failed": 0, "cancelled": 0}
    rows = list_jobs(store, statuses={"running", "queued"})

    for row in rows:
        tool_id = str(row["tool_id"])
        job_id = str(row["job_id"])
        status = row.get("status")
        try:
            meta = store.read_meta(tool_id, job_id)
        except (OSError, FileNotFoundError, ValueError):
            continue

        if status == "running":
            if _pid_alive(meta.get("pid")):
                continue
            _mark(
                store,
                tool_id,
                job_id,
                status="failed",
                error_message=_RUNNING_MSG,
                log_line=f"\n{_RUNNING_MSG}\n",
            )
            updated["failed"] += 1
        elif status == "queued":
            _mark(
                store,
                tool_id,
                job_id,
                status="cancelled",
                error_message=_QUEUED_MSG,
                log_line=f"\n{_QUEUED_MSG}\n",
            )
            updated["cancelled"] += 1

    total = updated["failed"] + updated["cancelled"]
    if total:
        logger.info(
            "Reconciled %s orphaned job(s): %s failed, %s cancelled",
            total,
            updated["failed"],
            updated["cancelled"],
        )
    return updated


def _mark(
    store: JobStore,
    tool_id: str,
    job_id: str,
    *,
    status: str,
    error_message: str,
    log_line: str,
) -> dict[str, Any]:
    store.append_log(tool_id, job_id, log_line)
    return store.update_meta(
        tool_id,
        job_id,
        status=status,
        error_message=error_message,
        exit_code=-1,
        finished_at=_utc_now(),
        pid=None,
        queue_reason=None,
    )

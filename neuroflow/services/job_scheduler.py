"""Promote queued jobs when host resources allow."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from neuroflow.config import Settings, get_settings
from neuroflow.services.host_resources import can_start_job
from neuroflow.services.job_list import list_jobs
from neuroflow.services.jobs import JobStore

logger = logging.getLogger(__name__)

# In-process starters keyed by (tool_id, job_id).
_PENDING: dict[tuple[str, str], Callable[[], None]] = {}
_LOCK = threading.Lock()
_SCHEDULER_STOP = threading.Event()
_SCHEDULER_THREAD: threading.Thread | None = None


def register_pending_launch(tool_id: str, job_id: str, starter: Callable[[], None]) -> None:
    with _LOCK:
        _PENDING[(tool_id, job_id)] = starter


def clear_pending_launch(tool_id: str, job_id: str) -> None:
    with _LOCK:
        _PENDING.pop((tool_id, job_id), None)


def pending_count() -> int:
    with _LOCK:
        return len(_PENDING)


def try_start_job(
    *,
    settings: Settings,
    store: JobStore,
    tool_id: str,
    job_id: str,
    starter: Callable[[], None],
    queue_if_busy: bool = True,
) -> str:
    """
    Start immediately when resources allow; otherwise queue the starter.

    Returns the resulting status: 'running' (starter invoked) or 'queued'.
    Raises RuntimeError when resources block and queue is full / disabled.
    """
    ok, reason = can_start_job(settings)
    queued = list_jobs(store, statuses={"queued"})
    queued_others = [j for j in queued if not (j["tool_id"] == tool_id and j["job_id"] == job_id)]

    if ok and not queued_others:
        starter()
        clear_pending_launch(tool_id, job_id)
        return "running"

    if not queue_if_busy:
        raise RuntimeError(reason or "Host resources exhausted")

    if len(queued_others) >= settings.neuroflow_max_queued_jobs:
        raise RuntimeError(
            f"Job queue is full ({settings.neuroflow_max_queued_jobs} waiting). "
            "Stop a running job or wait for resources."
        )

    register_pending_launch(tool_id, job_id, starter)
    store.update_meta(
        tool_id,
        job_id,
        status="queued",
        queue_reason=reason or "Waiting for earlier queued jobs",
        started_at=None,
    )
    return "queued"


def promote_queued_jobs(store: JobStore | None = None, settings: Settings | None = None) -> int:
    """Start the oldest queued job that has a registered starter when resources allow."""
    settings = settings or get_settings()
    if store is None:
        store = JobStore(settings)
    ok, _reason = can_start_job(settings)
    if not ok:
        return 0

    queued = list_jobs(store, statuses={"queued"})
    queued.sort(key=lambda row: row["created_at"] or 0)

    for row in queued:
        key = (row["tool_id"], row["job_id"])
        with _LOCK:
            starter = _PENDING.get(key)
        if starter is None:
            continue
        try:
            starter()
            clear_pending_launch(row["tool_id"], row["job_id"])
            store.update_meta(row["tool_id"], row["job_id"], queue_reason=None)
            return 1
        except Exception:
            logger.exception("Failed to promote job %s/%s", row["tool_id"], row["job_id"])
    return 0


def _scheduler_loop(interval_seconds: float = 5.0) -> None:
    while not _SCHEDULER_STOP.wait(interval_seconds):
        try:
            promote_queued_jobs()
        except Exception:
            logger.exception("Job scheduler tick failed")


def start_scheduler() -> None:
    global _SCHEDULER_THREAD
    if _SCHEDULER_THREAD and _SCHEDULER_THREAD.is_alive():
        return
    _SCHEDULER_STOP.clear()
    _SCHEDULER_THREAD = threading.Thread(
        target=_scheduler_loop,
        name="neuroflow-job-scheduler",
        daemon=True,
    )
    _SCHEDULER_THREAD.start()
    logger.info("Job resource scheduler started")


def stop_scheduler() -> None:
    _SCHEDULER_STOP.set()


def reset_pending_for_tests() -> None:
    """Clear in-memory pending map (tests only)."""
    with _LOCK:
        _PENDING.clear()

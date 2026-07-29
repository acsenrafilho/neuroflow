"""Tests for orphaned job reconciliation on startup."""

from pathlib import Path
from unittest.mock import patch

from neuroflow.config import Settings
from neuroflow.services.job_reconcile import reconcile_orphaned_jobs
from neuroflow.services.jobs import JobStore


def test_reconcile_marks_running_without_pid_as_failed(data_root: Path) -> None:
    settings = Settings(neuroflow_data_root=data_root)
    store = JobStore(settings)
    job_id = store.create_job("fsl", {"module_id": "fsl-bet"})
    store.update_meta(
        "fsl",
        job_id,
        status="running",
        pid=None,
        started_at="2026-01-01T00:00:00+00:00",
    )

    counts = reconcile_orphaned_jobs(store)

    assert counts["failed"] == 1
    meta = store.read_meta("fsl", job_id)
    assert meta["status"] == "failed"
    assert meta["finished_at"]
    assert "Orphaned" in (meta.get("error_message") or "")


def test_reconcile_marks_queued_as_cancelled(data_root: Path) -> None:
    settings = Settings(neuroflow_data_root=data_root)
    store = JobStore(settings)
    job_id = store.create_job("freesurfer", {"subject_id": "sub-001"})
    store.update_meta("freesurfer", job_id, status="queued", queue_reason="Waiting")

    counts = reconcile_orphaned_jobs(store)

    assert counts["cancelled"] == 1
    meta = store.read_meta("freesurfer", job_id)
    assert meta["status"] == "cancelled"
    assert meta.get("queue_reason") is None


def test_reconcile_keeps_running_with_live_pid(data_root: Path) -> None:
    settings = Settings(neuroflow_data_root=data_root)
    store = JobStore(settings)
    job_id = store.create_job("fsl", {"module_id": "fsl-bet"})
    store.update_meta("fsl", job_id, status="running", pid=1)

    with patch("neuroflow.services.job_reconcile._pid_alive", return_value=True):
        counts = reconcile_orphaned_jobs(store)

    assert counts == {"failed": 0, "cancelled": 0}
    assert store.read_meta("fsl", job_id)["status"] == "running"


def test_reconcile_skips_completed(data_root: Path) -> None:
    settings = Settings(neuroflow_data_root=data_root)
    store = JobStore(settings)
    job_id = store.create_job("fsl", {"module_id": "fsl-bet"})
    store.update_meta("fsl", job_id, status="completed", finished_at="2026-01-01T00:00:00+00:00")

    counts = reconcile_orphaned_jobs(store)

    assert counts == {"failed": 0, "cancelled": 0}
    assert store.read_meta("fsl", job_id)["status"] == "completed"

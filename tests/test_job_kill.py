"""Job kill service and API tests."""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.api.deps import get_job_store
from neuroflow.api.main import app
from neuroflow.config import Settings
from neuroflow.services.job_kill import JobKillError, request_job_kill, skip_if_cancelled
from neuroflow.services.jobs import JobStore


@pytest.fixture
def job_store(data_root) -> JobStore:
    return JobStore(Settings(neuroflow_data_root=data_root))


def test_request_job_kill_terminates_process(job_store: JobStore) -> None:
    job_id = job_store.create_job("fsl", {"module_id": "fsl-bet"})
    job_store.update_meta("fsl", job_id, status="running", pid=424242)

    with patch("neuroflow.services.job_kill._terminate_process_tree") as mock_kill:
        meta = request_job_kill(job_store, "fsl", job_id)
        mock_kill.assert_called_once_with(424242)

    assert meta["status"] == "cancelled"
    assert meta["error_message"] == "Stopped by user"
    assert meta["pid"] is None
    assert meta["cancel_requested"] is True
    assert "Job stopped by user." in job_store.read_log("fsl", job_id)


def test_request_job_kill_completed_raises(job_store: JobStore) -> None:
    job_id = job_store.create_job("fsl", {})
    job_store.update_meta("fsl", job_id, status="completed")

    with pytest.raises(JobKillError) as exc:
        request_job_kill(job_store, "fsl", job_id)

    assert exc.value.status_code == 409
    assert exc.value.code == "job_not_killable"


def test_request_job_kill_missing_job(job_store: JobStore) -> None:
    with pytest.raises(JobKillError) as exc:
        request_job_kill(job_store, "fsl", "missing-id")

    assert exc.value.status_code == 404


def test_skip_if_cancelled(job_store: JobStore) -> None:
    job_id = job_store.create_job("ants", {})
    job_store.update_meta("ants", job_id, status="running", cancel_requested=True)

    assert skip_if_cancelled(job_store, "ants", job_id) is True


@patch("neuroflow.tools.fsl.ensure_module_available")
@patch("neuroflow.tools.fsl.build_argv", return_value=["bet", "input.nii", "output.nii"])
def test_batch_worker_stops_when_cancel_requested(
    _mock_argv: object,
    _mock_ensure: object,
    job_store: JobStore,
    data_root,
) -> None:
    job_id = job_store.create_job("fsl", {})
    started_second = threading.Event()
    input_a = data_root / "a.nii"
    input_b = data_root / "b.nii"
    input_a.write_text("a")
    input_b.write_text("b")

    def fake_run_one(**kwargs: object) -> int:
        index = kwargs["scan_index"]
        if index == 1:
            job_store.update_meta("fsl", job_id, cancel_requested=True)
            return -15
        started_second.set()
        return 0

    from neuroflow.tools import fsl as fsl_module

    original = fsl_module._run_one_fsl
    fsl_module._run_one_fsl = fake_run_one  # type: ignore[assignment]
    try:
        with patch("neuroflow.tools.fsl.ensure_module_available"):
            fsl_module.launch_fsl_job(
                settings=Settings(
                    neuroflow_data_root=data_root,
                    neuroflow_datasets_root=data_root.parent / "datasets",
                ),
                store=job_store,
                job_id=job_id,
                module_id="fsl-bet",
                batch_items=[{"input": input_a}, {"input": input_b}],
                output_prefix="out",
                parameters={},
                workspace="demo_lab",
                subject_id="sub-001",
            )
        time.sleep(0.5)
    finally:
        fsl_module._run_one_fsl = original

    assert not started_second.is_set()
    meta = job_store.read_meta("fsl", job_id)
    assert meta.get("cancel_requested") is True


def test_kill_job_api_success(client: TestClient, job_store: JobStore) -> None:
    app.dependency_overrides[get_job_store] = lambda: job_store
    job_id = job_store.create_job("fsl", {})
    job_store.update_meta("fsl", job_id, status="running", pid=99999)

    try:
        with patch("neuroflow.services.job_kill._terminate_process_tree"):
            response = client.post(f"/api/v1/tools/fsl/jobs/{job_id}/kill")
    finally:
        app.dependency_overrides.pop(get_job_store, None)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["job_id"] == job_id


def test_kill_job_api_not_found(client: TestClient, job_store: JobStore) -> None:
    app.dependency_overrides[get_job_store] = lambda: job_store
    try:
        response = client.post("/api/v1/tools/fsl/jobs/does-not-exist/kill")
    finally:
        app.dependency_overrides.pop(get_job_store, None)
    assert response.status_code == 404


def test_kill_job_api_already_finished(client: TestClient, job_store: JobStore) -> None:
    app.dependency_overrides[get_job_store] = lambda: job_store
    job_id = job_store.create_job("freesurfer", {})
    job_store.update_meta("freesurfer", job_id, status="completed")

    try:
        response = client.post(f"/api/v1/tools/freesurfer/jobs/{job_id}/kill")
    finally:
        app.dependency_overrides.pop(get_job_store, None)

    assert response.status_code == 409


def test_kill_job_api_invalid_tool(client: TestClient) -> None:
    response = client.post("/api/v1/tools/not-a-tool/jobs/abc/kill")
    assert response.status_code == 422

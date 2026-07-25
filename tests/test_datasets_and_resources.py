"""Dataset path helpers and host resource / job list API tests."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.config import Settings
from neuroflow.services.datasets import (
    DatasetStore,
    modality_for_module,
    normalize_subject_id,
    sanitize_workspace,
)
from neuroflow.services.host_resources import HostResources, sample_host_resources
from neuroflow.services.jobs import JobStore


def test_sanitize_workspace() -> None:
    assert sanitize_workspace(" ana silva ") == "ana_silva"
    with pytest.raises(ValueError):
        sanitize_workspace("bad/name")


def test_normalize_subject_id() -> None:
    assert normalize_subject_id("001") == "sub-001"
    assert normalize_subject_id("sub-002") == "sub-002"


def test_modality_for_module() -> None:
    assert modality_for_module("fsl", "fsl-bet") == "anat"
    assert modality_for_module("fsl", "fsl-eddy") == "dwi"


def test_dataset_store_trees(tmp_path: Path) -> None:
    settings = Settings(neuroflow_datasets_root=tmp_path / "datasets")
    store = DatasetStore(settings)
    anat = store.ensure_subject_tree("lab_a", "001", "anat")
    assert anat.name == "anat"
    assert anat.parent.name == "sub-001"
    deriv = store.derivative_dir("lab_a", "fsl", "fsl-bet")
    assert deriv.as_posix().endswith("derivatives/fsl/bet")
    fs_dir = store.freesurfer_subjects_dir("lab_a")
    assert fs_dir.name == "freesurfer"


def test_host_resources_endpoint(client: TestClient) -> None:
    fake = HostResources(
        memory_percent=10.0,
        cpu_percent=5.0,
        ram_max_percent=80.0,
        cpu_max_percent=90.0,
        can_start_job=True,
        block_reason=None,
    )
    with patch(
        "neuroflow.api.v1.host.sample_host_resources",
        return_value=fake,
    ):
        response = client.get("/api/v1/host/resources")
    assert response.status_code == 200
    body = response.json()
    assert body["can_start_job"] is True
    assert body["can_accept_job"] is True
    assert body["memory_percent"] == 10.0


def test_list_jobs_endpoint(client: TestClient, data_root: Path) -> None:
    settings = Settings(neuroflow_data_root=data_root)
    store = JobStore(settings)
    job_id = store.create_job("fsl", {"module_id": "fsl-bet"})
    store.update_meta(
        "fsl",
        job_id,
        status="running",
        workspace="lab_a",
        subject_id="sub-001",
        parameters={"module_id": "fsl-bet", "workspace": "lab_a", "subject_id": "sub-001"},
    )

    # Override job store dependency to use same root as client… client already uses data_root.
    response = client.get("/api/v1/jobs?status=running,queued")
    assert response.status_code == 200
    rows = response.json()
    assert any(r["job_id"] == job_id for r in rows)
    match = next(r for r in rows if r["job_id"] == job_id)
    assert match["workspace"] == "lab_a"
    assert match["subject_id"] == "sub-001"
    assert "job_id=" in match["page_path"]


def test_sample_host_resources_thresholds() -> None:
    settings = Settings(neuroflow_ram_max_percent=50.0, neuroflow_cpu_max_percent=50.0)
    with (
        patch("neuroflow.services.host_resources._memory_percent", return_value=80.0),
        patch("neuroflow.services.host_resources._cpu_percent", return_value=10.0),
    ):
        sample = sample_host_resources(settings, cpu_interval=0.01)
    assert sample.can_start_job is False
    assert sample.block_reason and "RAM" in sample.block_reason

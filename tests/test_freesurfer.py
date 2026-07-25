"""FreeSurfer argv building and job API tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.tools.freesurfer import FreeSurferJobParams, build_recon_all_argv


def test_build_recon_all_argv_full() -> None:
    argv = build_recon_all_argv(
        input_path=Path("/data/input/sub-001_T1w.nii.gz"),
        recon_options="all",
    )
    assert argv[0] == "recon-all"
    assert argv[1:3] == ["-s", "freesurfer"]
    assert "-i" in argv
    assert "-all" in argv
    assert "-openmp" not in argv
    assert "sub-001" not in argv


def test_build_recon_all_argv_autorecon1() -> None:
    argv = build_recon_all_argv(
        input_path=Path("/tmp/t1.nii.gz"),
        recon_options="autorecon1",
    )
    assert argv[1:3] == ["-s", "freesurfer"]
    assert "-autorecon1" in argv


def test_subject_id_validation() -> None:
    with pytest.raises(ValueError):
        FreeSurferJobParams(subject_id="bad id!", recon_options="all")


def test_subject_id_normalizes_prefix() -> None:
    params = FreeSurferJobParams(subject_id="001", recon_options="all")
    assert params.subject_id == "sub-001"


@patch("neuroflow.tools.freesurfer.ensure_recon_all_available")
@patch("neuroflow.api.v1.tools.launch_freesurfer_job")
def test_create_freesurfer_job_api(
    mock_launch: object,
    _mock_ensure: object,
    client: TestClient,
) -> None:
    mock_launch.return_value = ["recon-all", "-s", "sub-001"]

    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.parent.mkdir(parents=True, exist_ok=True)
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)

    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/freesurfer/jobs",
            data={
                "subject_ids": json.dumps(["sub-001"]),
                "recon_options": "all",
                "workspace": "demo_lab",
            },
            files=[("files", ("sub-001_T1w.nii.gz", handle, "application/octet-stream"))],
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["job_id"]
    assert body["tool_id"] == "freesurfer"
    mock_launch.assert_called_once()
    assert mock_launch.call_args.kwargs["workspace"] == "demo_lab"

    status = client.get(f"/api/v1/tools/freesurfer/jobs/{body['job_id']}")
    assert status.status_code == 200
    assert "elapsed_seconds" in status.json()

    log = client.get(f"/api/v1/tools/freesurfer/jobs/{body['job_id']}/log")
    assert log.status_code == 200
    assert "job_id" in log.json()


def test_create_job_subject_ids_length_mismatch(client: TestClient) -> None:
    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)
    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/freesurfer/jobs",
            data={
                "subject_ids": json.dumps(["sub-001", "sub-002"]),
                "recon_options": "all",
                "workspace": "demo_lab",
            },
            files=[("files", ("a.nii.gz", handle, "application/octet-stream"))],
        )
    assert response.status_code == 422


@patch("neuroflow.tools.freesurfer.ensure_recon_all_available")
@patch("neuroflow.api.v1.tools.launch_freesurfer_job")
def test_batch_launch_passes_multiple_scans(
    mock_launch: object,
    _mock_ensure: object,
    client: TestClient,
) -> None:
    def _fake_launch(**kwargs: object) -> list[str]:
        store = kwargs["store"]
        job_id = kwargs["job_id"]
        store.update_meta(
            "freesurfer",
            job_id,
            batch_total=len(kwargs["scans"]),
            status="running",
        )
        return ["recon-all"]

    mock_launch.side_effect = _fake_launch

    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)

    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/freesurfer/jobs",
            data={
                "subject_ids": json.dumps(["sub-001", "sub-002"]),
                "recon_options": "autorecon1",
                "workspace": "demo_lab",
            },
            files=[
                ("files", ("sub-001_T1w.nii.gz", handle, "application/octet-stream")),
                ("files", ("sub-002_T1w.nii.gz", handle, "application/octet-stream")),
            ],
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["batch_total"] == 2


def test_list_tools(client: TestClient) -> None:
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    tools = response.json()
    ids = {t["id"] for t in tools}
    assert ids == {"freesurfer", "fsl", "sct"}

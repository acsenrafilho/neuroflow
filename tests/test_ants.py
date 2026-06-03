"""ANTs argv building and job API tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from neuroflow.config import Settings
from neuroflow.tools.ants import (
    ROLE_FIXED,
    ROLE_INPUT,
    ROLE_MOVING,
    ROLE_TRANSFORM,
    AntsJobParams,
    build_argv,
    group_uploads_into_batch,
)


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_ants_job_params_validation() -> None:
    with pytest.raises(ValueError):
        AntsJobParams(module_id="unknown", output_prefix="out")


def test_build_n4_argv(work_dir: Path) -> None:
    input_path = work_dir / "t1.nii.gz"
    input_path.write_bytes(b"x")
    argv = build_argv(
        module_id="ants-n4",
        files={ROLE_INPUT: input_path},
        work_dir=work_dir,
        output_prefix="subj",
        parameters={},
        settings=Settings(),
    )
    assert argv[0] == "N4BiasFieldCorrection"
    assert "-i" in argv
    assert str(input_path.resolve()) in argv


def test_build_syn_quick_argv(work_dir: Path) -> None:
    fixed = work_dir / "fixed.nii.gz"
    moving = work_dir / "moving.nii.gz"
    fixed.write_bytes(b"x")
    moving.write_bytes(b"x")
    argv = build_argv(
        module_id="ants-registration-syn-quick",
        files={ROLE_FIXED: fixed, ROLE_MOVING: moving},
        work_dir=work_dir,
        output_prefix="reg",
        parameters={"dimension": 3},
        settings=Settings(),
    )
    assert argv[0] == "antsRegistrationSyNQuick.sh"
    assert "-f" in argv
    assert str(fixed.resolve()) in argv


def test_build_image_math_rejects_unknown_operation(work_dir: Path) -> None:
    input_path = work_dir / "t1.nii.gz"
    input_path.write_bytes(b"x")
    with pytest.raises(ValueError, match="Unsupported ImageMath"):
        build_argv(
            module_id="ants-image-math",
            files={ROLE_INPUT: input_path},
            work_dir=work_dir,
            output_prefix="out",
            parameters={"operation": "evil"},
            settings=Settings(),
        )


def test_group_batch_driver(work_dir: Path) -> None:
    inputs = [work_dir / f"t{i}.nii.gz" for i in range(2)]
    for p in inputs:
        p.write_bytes(b"x")
    batches = group_uploads_into_batch("ants-n4", {ROLE_INPUT: inputs})
    assert len(batches) == 2


@patch("neuroflow.api.v1.tools.launch_ants_job")
def test_create_ants_job_api(mock_launch: object, client: TestClient) -> None:
    def _fake(**kwargs: object) -> list[str]:
        store = kwargs["store"]
        job_id = kwargs["job_id"]
        store.update_meta("ants", job_id, batch_total=len(kwargs["batch_items"]), status="running")
        return ["N4BiasFieldCorrection"]

    mock_launch.side_effect = _fake

    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/ants/jobs",
            data={
                "file_roles": json.dumps(["input"]),
                "module_id": "ants-n4",
                "output_prefix": "corrected",
            },
            files=[("files", ("t1.nii.gz", handle, "application/octet-stream"))],
        )

    assert response.status_code == 201, response.text
    assert mock_launch.call_args.kwargs["module_id"] == "ants-n4"


def test_launch_ants_job_batch_meta(work_dir: Path) -> None:
    from neuroflow.services.jobs import JobStore
    from neuroflow.tools.ants import launch_ants_job

    settings = Settings()
    store = JobStore(settings)
    job_id = store.create_job("ants", {"module_id": "ants-n4"})
    input_path = work_dir / "sub-001_T1w.nii.gz"
    input_path.write_bytes(b"x")

    with patch("neuroflow.tools.ants._run_one_ants", return_value=0):
        launch_ants_job(
            settings=settings,
            store=store,
            job_id=job_id,
            module_id="ants-n4",
            batch_items=[{ROLE_INPUT: input_path}],
            output_prefix="n4",
            parameters={},
        )

    meta = store.read_meta("ants", job_id)
    assert meta["batch_total"] == 1
    assert meta["status"] == "running"

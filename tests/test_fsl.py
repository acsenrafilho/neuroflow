"""FSL argv building and job API tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.tools.fsl import (
    ROLE_BVALS,
    ROLE_BVECS,
    ROLE_INPUT,
    FslJobParams,
    build_argv,
    group_uploads_into_batch,
    infer_nifti_suffix,
    output_prefix_for_batch,
    resolve_fsl_output_path,
    strip_nifti_extension,
)


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_fsl_job_params_validation() -> None:
    with pytest.raises(ValueError):
        FslJobParams(module_id="unknown", output_prefix="out")


def test_strip_nifti_extension() -> None:
    assert strip_nifti_extension("brain.nii.gz") == "brain"
    assert strip_nifti_extension("brain.nii") == "brain"
    assert strip_nifti_extension("brain") == "brain"


def test_infer_nifti_suffix_from_input() -> None:
    files = {ROLE_INPUT: Path("/tmp/subj_T1w.nii")}
    assert infer_nifti_suffix(files, role_priority=(ROLE_INPUT,)) == ".nii"
    files_gz = {ROLE_INPUT: Path("/tmp/subj_T1w.nii.gz")}
    assert infer_nifti_suffix(files_gz, role_priority=(ROLE_INPUT,)) == ".nii.gz"


def test_resolve_output_image_module(work_dir: Path) -> None:
    input_path = work_dir / "t1.nii.gz"
    input_path.write_bytes(b"x")
    out = resolve_fsl_output_path(
        "fsl-susan", work_dir / "output", "denoised", {ROLE_INPUT: input_path}
    )
    assert str(out).endswith("denoised.nii.gz")


def test_resolve_output_prefix_module_strips_extension(work_dir: Path) -> None:
    input_path = work_dir / "t1.nii.gz"
    out = resolve_fsl_output_path(
        "fsl-bet", work_dir / "output", "brain.nii.gz", {ROLE_INPUT: input_path}
    )
    assert out.name == "brain"
    assert not str(out).endswith(".nii.gz")


def test_group_batch_driver_with_shared_sidecar(work_dir: Path) -> None:
    inputs = [work_dir / f"dwi{i}.nii.gz" for i in range(3)]
    for p in inputs:
        p.write_bytes(b"x")
    bvals = work_dir / "bvals"
    bvecs = work_dir / "bvecs"
    bvals.write_text("0\n")
    bvecs.write_text("0\n")

    batches = group_uploads_into_batch(
        "fsl-fdt",
        {
            ROLE_INPUT: inputs,
            ROLE_BVALS: [bvals],
            ROLE_BVECS: [bvecs],
        },
    )
    assert len(batches) == 3
    assert batches[0][ROLE_BVALS] == bvals
    assert batches[1][ROLE_INPUT].name == "dwi1.nii.gz"


def test_group_zip_mode_flirt(work_dir: Path) -> None:
    mov = [work_dir / "m1.nii.gz", work_dir / "m2.nii.gz"]
    ref = [work_dir / "r1.nii.gz", work_dir / "r2.nii.gz"]
    for p in mov + ref:
        p.write_bytes(b"x")

    from neuroflow.tools.fsl import ROLE_MOVING, ROLE_REFERENCE

    batches = group_uploads_into_batch(
        "fsl-flirt",
        {ROLE_MOVING: mov, ROLE_REFERENCE: ref},
    )
    assert len(batches) == 2


def test_output_prefix_for_batch(work_dir: Path) -> None:
    f = work_dir / "sub-001_T1w.nii.gz"
    prefix = output_prefix_for_batch(
        "result",
        {ROLE_INPUT: f},
        "fsl-bet",
        index=0,
        batch_total=2,
    )
    assert prefix == "result_sub-001_T1w"


def test_batch_meta_matches_batch_item_status_schema(work_dir: Path) -> None:
    from neuroflow.config import Settings
    from neuroflow.services.job_monitoring import batch_items_from_meta
    from neuroflow.services.jobs import JobStore

    settings = Settings()
    store = JobStore(settings)
    job_id = store.create_job("fsl", {"module_id": "fsl-bet"})
    input_path = work_dir / "sub-001_T1w.nii.gz"
    input_path.write_bytes(b"x")

    from neuroflow.tools.fsl import launch_fsl_job

    with patch("neuroflow.tools.fsl._run_one_fsl", return_value=0), patch(
        "neuroflow.tools.fsl.ensure_module_available"
    ):
        launch_fsl_job(
            settings=settings,
            store=store,
            job_id=job_id,
            module_id="fsl-bet",
            batch_items=[{ROLE_INPUT: input_path}],
            output_prefix="brain",
            parameters={},
            workspace="demo_lab",
            subject_id="sub-001",
        )

    meta = store.read_meta("fsl", job_id)
    items = batch_items_from_meta(meta)
    assert len(items) == 1
    assert items[0].filename == "sub-001_T1w.nii.gz"
    assert items[0].subject_id == "sub-001"
    assert "sub-001/derivatives/fsl/bet" in str(meta.get("dataset_output_dir", "")).replace(
        "\\", "/"
    )


@patch("neuroflow.tools.fsl.ensure_module_available")
@patch("neuroflow.api.v1.tools.launch_fsl_job")
def test_create_fsl_batch_job_api(
    mock_launch: object, _mock_ensure: object, client: TestClient
) -> None:
    def _fake(**kwargs: object) -> list[str]:
        store = kwargs["store"]
        job_id = kwargs["job_id"]
        store.update_meta("fsl", job_id, batch_total=len(kwargs["batch_items"]), status="running")
        return ["bet"]

    mock_launch.side_effect = _fake

    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)

    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/fsl/jobs",
            data={
                "file_roles": json.dumps(["input", "input"]),
                "module_id": "fsl-bet",
                "output_prefix": "brain",
                "workspace": "demo_lab",
                "subject_id": "sub-001",
            },
            files=[
                ("files", ("a.nii.gz", handle, "application/octet-stream")),
                ("files", ("b.nii.gz", handle, "application/octet-stream")),
            ],
        )

    assert response.status_code == 201, response.text
    assert mock_launch.call_args.kwargs["batch_items"]
    assert len(mock_launch.call_args.kwargs["batch_items"]) == 2
    assert mock_launch.call_args.kwargs["workspace"] == "demo_lab"
    assert mock_launch.call_args.kwargs["subject_id"] == "sub-001"


def test_build_bet_argv(work_dir: Path) -> None:
    input_path = work_dir / "t1.nii.gz"
    input_path.write_bytes(b"x")
    from neuroflow.config import Settings

    settings = Settings()
    argv = build_argv(
        module_id="fsl-bet",
        files={ROLE_INPUT: input_path},
        work_dir=work_dir,
        output_prefix="brain",
        parameters={"fractional_intensity": 0.4, "generate_mask": True},
        settings=settings,
    )
    assert argv[0] == "bet"
    assert str(input_path) in argv
    assert "-m" in argv
    assert "-f" in argv and "0.4" in argv


def test_build_bet2_argv(work_dir: Path) -> None:
    input_path = work_dir / "t1.nii.gz"
    input_path.write_bytes(b"x")
    from neuroflow.config import Settings

    settings = Settings()
    argv = build_argv(
        module_id="fsl-bet",
        files={ROLE_INPUT: input_path},
        work_dir=work_dir,
        output_prefix="brain",
        parameters={"bet_mode": "bet2"},
        settings=settings,
    )
    assert argv[0] == "bet2"


def test_build_fast_argv(work_dir: Path) -> None:
    input_path = work_dir / "t1.nii.gz"
    input_path.write_bytes(b"x")
    from neuroflow.config import Settings

    settings = Settings()
    argv = build_argv(
        module_id="fsl-fast",
        files={ROLE_INPUT: input_path},
        work_dir=work_dir,
        output_prefix="seg",
        parameters={"tissue_type": 1, "n_segments": 3},
        settings=settings,
    )
    assert argv[0] == "fast"
    assert "-o" in argv
    assert "-t" in argv


def test_build_flirt_argv(work_dir: Path) -> None:
    from neuroflow.config import Settings
    from neuroflow.tools.fsl import ROLE_MOVING, ROLE_REFERENCE

    mov = work_dir / "mov.nii.gz"
    ref = work_dir / "ref.nii.gz"
    mov.write_bytes(b"x")
    ref.write_bytes(b"x")
    settings = Settings()
    argv = build_argv(
        module_id="fsl-flirt",
        files={ROLE_MOVING: mov, ROLE_REFERENCE: ref},
        work_dir=work_dir,
        output_prefix="reg",
        parameters={"dof": 6},
        settings=settings,
    )
    assert argv[0] == "flirt"
    assert "-omat" in argv
    out_idx = argv.index("-out")
    assert argv[out_idx + 1].endswith(".nii.gz")


def test_build_susan_argv_uses_nifti_extension(work_dir: Path) -> None:
    input_path = work_dir / "vol.nii"
    input_path.write_bytes(b"x")
    from neuroflow.config import Settings

    settings = Settings()
    argv = build_argv(
        module_id="fsl-susan",
        files={ROLE_INPUT: input_path},
        work_dir=work_dir,
        output_prefix="smooth",
        parameters={},
        settings=settings,
    )
    assert argv[2].endswith("smooth.nii")


@patch("neuroflow.tools.fsl.ensure_module_available")
@patch("neuroflow.api.v1.tools.launch_fsl_job")
def test_create_fsl_job_api(
    mock_launch: object, _mock_ensure: object, client: TestClient
) -> None:
    mock_launch.return_value = ["bet", "in.nii.gz", "out"]

    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)

    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/fsl/jobs",
            data={
                "file_roles": json.dumps(["input"]),
                "module_id": "fsl-bet",
                "output_prefix": "brain",
                "workspace": "demo_lab",
                "subject_id": "001",
                "parameters": json.dumps({"fractional_intensity": 0.5}),
            },
            files=[("files", ("t1.nii.gz", handle, "application/octet-stream"))],
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["tool_id"] == "fsl"
    mock_launch.assert_called_once()
    assert mock_launch.call_args.kwargs["subject_id"] == "sub-001"

    status = client.get(f"/api/v1/tools/fsl/jobs/{body['job_id']}")
    assert status.status_code == 200

    log = client.get(f"/api/v1/tools/fsl/jobs/{body['job_id']}/log")
    assert log.status_code == 200


def test_create_fsl_job_roles_mismatch(client: TestClient) -> None:
    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)
    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/fsl/jobs",
            data={
                "file_roles": json.dumps(["input", "reference"]),
                "module_id": "fsl-bet",
                "workspace": "demo_lab",
                "subject_id": "sub-001",
            },
            files=[("files", ("a.nii.gz", handle, "application/octet-stream"))],
        )
    assert response.status_code == 422

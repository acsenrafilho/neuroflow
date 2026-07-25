"""SCT argv building and job API tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.tools.sct import (
    ROLE_DEST,
    ROLE_INPUT,
    ROLE_SEG,
    ROLE_WARP,
    SctJobParams,
    build_argv,
    group_uploads_into_batch,
    output_prefix_for_batch,
    strip_nifti_extension,
)


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_sct_job_params_validation() -> None:
    with pytest.raises(ValueError):
        SctJobParams(module_id="unknown", output_prefix="out")


def test_strip_nifti_extension() -> None:
    assert strip_nifti_extension("cord.nii.gz") == "cord"
    assert strip_nifti_extension("cord.nii") == "cord"


def test_group_batch_deepseg(work_dir: Path) -> None:
    inputs = [work_dir / f"t2_{i}.nii.gz" for i in range(3)]
    for path in inputs:
        path.write_bytes(b"x")
    batches = group_uploads_into_batch("sct-deepseg", {ROLE_INPUT: inputs})
    assert len(batches) == 3
    assert batches[1][ROLE_INPUT].name == "t2_1.nii.gz"


def test_output_prefix_for_batch(work_dir: Path) -> None:
    path = work_dir / "sub-001_T2w.nii.gz"
    prefix = output_prefix_for_batch(
        "result",
        {ROLE_INPUT: path},
        "sct-deepseg",
        index=0,
        batch_total=2,
    )
    assert prefix == "result_sub-001_T2w"


def test_build_deepseg_argv(work_dir: Path) -> None:
    input_path = work_dir / "t2.nii.gz"
    input_path.write_bytes(b"x")
    argv = build_argv(
        module_id="sct-deepseg",
        files={ROLE_INPUT: input_path},
        work_dir=work_dir,
        output_prefix="cord",
        parameters={"task": "spinalcord"},
    )
    assert argv[0] == "sct_deepseg"
    assert argv[1] == "spinalcord"
    assert "-i" in argv
    assert "-o" in argv
    assert argv[argv.index("-o") + 1].endswith("cord_seg.nii.gz")


def test_build_propseg_argv(work_dir: Path) -> None:
    input_path = work_dir / "t2.nii.gz"
    input_path.write_bytes(b"x")
    argv = build_argv(
        module_id="sct-propseg",
        files={ROLE_INPUT: input_path},
        work_dir=work_dir,
        output_prefix="result",
        parameters={"contrast": "t2"},
    )
    assert argv[0] == "sct_propseg"
    assert "-c" in argv and "t2" in argv
    assert "-ofolder" in argv


def test_build_label_vertebrae_argv(work_dir: Path) -> None:
    anat = work_dir / "t2.nii.gz"
    seg = work_dir / "t2_seg.nii.gz"
    anat.write_bytes(b"x")
    seg.write_bytes(b"x")
    argv = build_argv(
        module_id="sct-label-vertebrae",
        files={ROLE_INPUT: anat, ROLE_SEG: seg},
        work_dir=work_dir,
        output_prefix="labels",
        parameters={"contrast": "t2"},
    )
    assert argv[0] == "sct_label_vertebrae"
    assert "-s" in argv
    assert "-ofolder" in argv


def test_build_register_to_template_argv(work_dir: Path) -> None:
    anat = work_dir / "t2.nii.gz"
    seg = work_dir / "t2_seg.nii.gz"
    anat.write_bytes(b"x")
    seg.write_bytes(b"x")
    argv = build_argv(
        module_id="sct-register-to-template",
        files={ROLE_INPUT: anat, ROLE_SEG: seg},
        work_dir=work_dir,
        output_prefix="reg",
        parameters={"contrast": "t2"},
    )
    assert argv[0] == "sct_register_to_template"
    assert "-ofolder" in argv


def test_build_warp_template_argv(work_dir: Path) -> None:
    dest = work_dir / "dest.nii.gz"
    warp = work_dir / "warp.nii.gz"
    dest.write_bytes(b"x")
    warp.write_bytes(b"x")
    argv = build_argv(
        module_id="sct-warp-template",
        files={ROLE_DEST: dest, ROLE_WARP: warp},
        work_dir=work_dir,
        output_prefix="label",
        parameters={},
    )
    assert argv[0] == "sct_warp_template"
    assert "-d" in argv
    assert "-w" in argv


def test_build_apply_transfo_argv(work_dir: Path) -> None:
    input_path = work_dir / "src.nii.gz"
    dest = work_dir / "dest.nii.gz"
    warp = work_dir / "warp.nii.gz"
    for path in (input_path, dest, warp):
        path.write_bytes(b"x")
    argv = build_argv(
        module_id="sct-apply-transfo",
        files={ROLE_INPUT: input_path, ROLE_DEST: dest, ROLE_WARP: warp},
        work_dir=work_dir,
        output_prefix="warped",
        parameters={"interpolation": "linear"},
    )
    assert argv[0] == "sct_apply_transfo"
    assert "-x" in argv and "linear" in argv


def test_build_process_segmentation_argv(work_dir: Path) -> None:
    seg = work_dir / "cord_seg.nii.gz"
    seg.write_bytes(b"x")
    argv = build_argv(
        module_id="sct-process-segmentation",
        files={ROLE_INPUT: seg},
        work_dir=work_dir,
        output_prefix="csa",
        parameters={"perslice": "1"},
    )
    assert argv[0] == "sct_process_segmentation"
    assert argv[argv.index("-o") + 1].endswith("csa_csa.csv")
    assert "-perslice" in argv


def test_build_create_mask_centerline_requires_role(work_dir: Path) -> None:
    input_path = work_dir / "t2.nii.gz"
    input_path.write_bytes(b"x")
    with pytest.raises(ValueError, match="centerline"):
        build_argv(
            module_id="sct-create-mask",
            files={ROLE_INPUT: input_path},
            work_dir=work_dir,
            output_prefix="mask",
            parameters={"process": "centerline"},
        )


@patch("neuroflow.tools.sct.ensure_module_available")
@patch("neuroflow.api.v1.tools.launch_sct_job")
def test_create_sct_job_api(
    mock_launch: object, _mock_ensure: object, client: TestClient
) -> None:
    mock_launch.return_value = ["sct_deepseg", "spinalcord", "-i", "in.nii.gz"]

    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.parent.mkdir(parents=True, exist_ok=True)
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)

    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/sct/jobs",
            data={
                "file_roles": json.dumps(["input"]),
                "module_id": "sct-deepseg",
                "output_prefix": "cord",
                "workspace": "demo_lab",
                "subject_id": "001",
                "parameters": json.dumps({"task": "spinalcord"}),
            },
            files=[("files", ("t2.nii.gz", handle, "application/octet-stream"))],
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["tool_id"] == "sct"
    mock_launch.assert_called_once()
    assert mock_launch.call_args.kwargs["subject_id"] == "sub-001"

    status = client.get(f"/api/v1/tools/sct/jobs/{body['job_id']}")
    assert status.status_code == 200

    log = client.get(f"/api/v1/tools/sct/jobs/{body['job_id']}/log")
    assert log.status_code == 200


@patch("neuroflow.tools.sct.ensure_module_available")
@patch("neuroflow.api.v1.tools.launch_sct_job")
def test_create_sct_batch_job_api(
    mock_launch: object, _mock_ensure: object, client: TestClient
) -> None:
    def _fake(**kwargs: object) -> list[str]:
        store = kwargs["store"]
        job_id = kwargs["job_id"]
        store.update_meta("sct", job_id, batch_total=len(kwargs["batch_items"]), status="running")
        return ["sct_deepseg"]

    mock_launch.side_effect = _fake

    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.parent.mkdir(parents=True, exist_ok=True)
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)

    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/sct/jobs",
            data={
                "file_roles": json.dumps(["input", "input"]),
                "module_id": "sct-deepseg",
                "output_prefix": "cord",
                "workspace": "demo_lab",
                "subject_id": "sub-001",
            },
            files=[
                ("files", ("a.nii.gz", handle, "application/octet-stream")),
                ("files", ("b.nii.gz", handle, "application/octet-stream")),
            ],
        )

    assert response.status_code == 201, response.text
    assert len(mock_launch.call_args.kwargs["batch_items"]) == 2


def test_create_sct_job_roles_mismatch(client: TestClient) -> None:
    nii = Path(__file__).parent / "fixtures" / "tiny.nii.gz"
    nii.parent.mkdir(parents=True, exist_ok=True)
    nii.write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 20)
    with nii.open("rb") as handle:
        response = client.post(
            "/api/v1/tools/sct/jobs",
            data={
                "file_roles": json.dumps(["input", "seg"]),
                "module_id": "sct-deepseg",
                "workspace": "demo_lab",
                "subject_id": "sub-001",
            },
            files=[("files", ("a.nii.gz", handle, "application/octet-stream"))],
        )
    assert response.status_code == 422

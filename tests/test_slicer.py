"""3D Slicer argv building and job API tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.tools.slicer import (
    ROLE_BVALS,
    ROLE_BVECS,
    ROLE_BASELINE,
    ROLE_DWI,
    ROLE_INPUT,
    ROLE_MASK,
    SlicerJobParams,
    build_argv,
    group_uploads_into_batch,
    strip_nrrd_extension,
)


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_slicer_job_params_validation() -> None:
    with pytest.raises(ValueError):
        SlicerJobParams(module_id="unknown", output_prefix="out")


def test_strip_nrrd_extension() -> None:
    assert strip_nrrd_extension("dwi.nrrd") == "dwi"
    assert strip_nrrd_extension("dwi") == "dwi"


def test_build_argv_dwi_convert(work_dir: Path) -> None:
    nii = work_dir / "dwi.nii.gz"
    nii.write_bytes(b"x")
    bvals = work_dir / "bvals"
    bvecs = work_dir / "bvecs"
    bvals.write_text("0\n")
    bvecs.write_text("0\n")

    argv = build_argv(
        module_id="slicer-dwi-convert",
        files={ROLE_INPUT: nii, ROLE_BVALS: bvals, ROLE_BVECS: bvecs},
        work_dir=work_dir,
        output_prefix="dwi",
        parameters={"conversion_mode": "FSLToNrrd", "allow_lossy": True},
    )
    assert argv[:3] == ["--launch", "DWIConvert", "--conversionMode"]
    assert "FSLToNrrd" in argv
    assert "--allowLossyConversion" in argv
    assert str(nii.resolve()) in argv
    assert str((work_dir / "output" / "dwi.nrrd").resolve()) in argv


def test_build_argv_dwi_mask(work_dir: Path) -> None:
    dwi = work_dir / "dwi.nrrd"
    dwi.write_bytes(b"x")

    argv = build_argv(
        module_id="slicer-dwi-mask",
        files={ROLE_DWI: dwi},
        work_dir=work_dir,
        output_prefix="dwi",
        parameters={"remove_islands": True},
    )
    assert argv[0:2] == ["--launch", "DiffusionWeightedVolumeMasking"]
    assert "--removeislands" in argv
    assert str((work_dir / "output" / "dwi_baseline.nrrd").resolve()) in argv
    assert str((work_dir / "output" / "dwi_brain_mask.nrrd").resolve()) in argv


def test_build_argv_dwi_to_dti(work_dir: Path) -> None:
    dwi = work_dir / "dwi.nrrd"
    baseline = work_dir / "dwi_baseline.nrrd"
    mask = work_dir / "dwi_brain_mask.nrrd"
    for p in (dwi, baseline, mask):
        p.write_bytes(b"x")

    argv = build_argv(
        module_id="slicer-dwi-to-dti",
        files={ROLE_DWI: dwi, ROLE_BASELINE: baseline, ROLE_MASK: mask},
        work_dir=work_dir,
        output_prefix="dti",
        parameters={"enumeration": "LS"},
    )
    assert argv[:2] == ["--launch", "DWIToDTIEstimation"]
    assert "--enumeration" in argv
    assert "LS" in argv
    assert str((work_dir / "output" / "dti.nrrd").resolve()) in argv


def test_group_batch_dwi_convert_shared_bvals(work_dir: Path) -> None:
    inputs = [work_dir / f"dwi{i}.nii.gz" for i in range(2)]
    for p in inputs:
        p.write_bytes(b"x")
    bvals = work_dir / "bvals"
    bvecs = work_dir / "bvecs"
    bvals.write_text("0\n")
    bvecs.write_text("0\n")

    batches = group_uploads_into_batch(
        "slicer-dwi-convert",
        {
            ROLE_INPUT: inputs,
            ROLE_BVALS: [bvals],
            ROLE_BVECS: [bvecs],
        },
    )
    assert len(batches) == 2
    assert batches[0][ROLE_BVALS] == bvals


@patch("neuroflow.api.v1.tools.launch_slicer_job")
def test_create_slicer_job_api(mock_launch: object, client: TestClient) -> None:
    mock_launch.return_value = ["Slicer", "--launch", "DWIConvert"]

    response = client.post(
        "/api/v1/tools/slicer/jobs",
        data={
            "file_roles": json.dumps(["input", "bvals", "bvecs"]),
            "module_id": "slicer-dwi-convert",
            "output_prefix": "dwi",
            "parameters": json.dumps({"conversion_mode": "FSLToNrrd"}),
        },
        files=[
            ("files", ("dwi.nii.gz", b"fake", "application/octet-stream")),
            ("files", ("bvals.bval", b"0\n", "text/plain")),
            ("files", ("bvecs.bvec", b"0\n", "text/plain")),
        ],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["tool_id"] == "slicer"
    assert body["job_id"]

    status = client.get(f"/api/v1/tools/slicer/jobs/{body['job_id']}")
    assert status.status_code == 200

    log = client.get(f"/api/v1/tools/slicer/jobs/{body['job_id']}/log")
    assert log.status_code == 200

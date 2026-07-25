"""ITK argv building and job API tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.config import Settings
from neuroflow.tools.itk import (
    ROLE_INPUT,
    ROLE_MASK,
    ItkJobParams,
    build_argv,
    group_uploads_into_batch,
)


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def itk_settings(tmp_path: Path) -> Settings:
    binary = tmp_path / "DiffusionComplexityMapping"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        json.dumps({"itk-diffusion-complexity-mapping": str(binary)}),
        encoding="utf-8",
    )
    return Settings(neuroflow_itk_binaries_config=config_path)


def test_itk_job_params_validation() -> None:
    with pytest.raises(ValueError):
        ItkJobParams(module_id="unknown", output_prefix="out")


def test_build_argv_with_mask(work_dir: Path, itk_settings: Settings) -> None:
    nii = work_dir / "dwi.nii.gz"
    nii.write_bytes(b"x")
    mask = work_dir / "mask.nii.gz"
    mask.write_bytes(b"m")

    argv = build_argv(
        module_id="itk-diffusion-complexity-mapping",
        files={ROLE_INPUT: nii, ROLE_MASK: mask},
        work_dir=work_dir,
        output_prefix="dcm",
        parameters={"q_value": 2.5, "use_mask": True},
        settings=itk_settings,
    )
    assert argv[0].endswith("DiffusionComplexityMapping")
    assert argv[1] == str(nii.resolve())
    assert argv[2] == str(mask.resolve())
    assert argv[3] == str((work_dir / "output" / "dcm.nii.gz").resolve())
    assert argv[4] == "2.5"


def test_build_argv_without_mask(work_dir: Path, itk_settings: Settings) -> None:
    nii = work_dir / "dwi.nii.gz"
    nii.write_bytes(b"x")

    argv = build_argv(
        module_id="itk-diffusion-complexity-mapping",
        files={ROLE_INPUT: nii},
        work_dir=work_dir,
        output_prefix="dcm",
        parameters={"q_value": 1.0, "use_mask": False},
        settings=itk_settings,
    )
    assert len(argv) == 4
    assert argv[1] == str(nii.resolve())
    assert argv[2] == str((work_dir / "output" / "dcm.nii.gz").resolve())
    assert argv[3] == "1.0"


def test_group_uploads_shared_mask(work_dir: Path) -> None:
    a = work_dir / "a.nii.gz"
    b = work_dir / "b.nii.gz"
    mask = work_dir / "mask.nii.gz"
    for p in (a, b, mask):
        p.write_bytes(b"x")

    items = group_uploads_into_batch(
        "itk-diffusion-complexity-mapping",
        {ROLE_INPUT: [a, b], ROLE_MASK: [mask]},
    )
    assert len(items) == 2
    assert items[0][ROLE_MASK] == mask
    assert items[1][ROLE_MASK] == mask


@patch("neuroflow.api.v1.tools.launch_itk_job")
def test_create_itk_job_api(
    mock_launch,
    client: TestClient,
    tmp_path: Path,
) -> None:
    binary = tmp_path / "DiffusionComplexityMapping"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        json.dumps({"itk-diffusion-complexity-mapping": str(binary)}),
        encoding="utf-8",
    )

    nii = tmp_path / "dwi.nii.gz"
    nii.write_bytes(b"fake")

    mock_launch.return_value = ["preview"]

    response = client.post(
            "/api/v1/tools/itk/jobs",
            data={
                "module_id": "itk-diffusion-complexity-mapping",
                "output_prefix": "out",
                "parameters": json.dumps({"q_value": 1.0, "use_mask": False}),
                "file_roles": json.dumps(["input"]),
                "workspace": "demo_lab",
                "subject_id": "sub-001",
            },
            files={"files": ("dwi.nii.gz", nii.read_bytes(), "application/gzip")},
    )

    assert response.status_code == 201
    mock_launch.assert_called_once()
    assert mock_launch.call_args.kwargs["workspace"] == "demo_lab"
    assert mock_launch.call_args.kwargs["subject_id"] == "sub-001"

"""dcm2niix argv, DICOM staging, and MRIcron job API tests."""

import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from neuroflow.tools.mricron import FILENAME_PATTERN, build_argv, prepare_dicom_dir


def test_build_argv_is_fixed(tmp_path: Path) -> None:
    output = tmp_path / "out"
    dicom = tmp_path / "dicom"
    argv = build_argv(output_dir=output, dicom_dir=dicom)
    assert argv == [
        "dcm2niix",
        "-z",
        "y",
        "-b",
        "y",
        "-ba",
        "y",
        "-f",
        FILENAME_PATTERN,
        "-o",
        str(output),
        str(dicom),
    ]
    assert FILENAME_PATTERN == "%n_%p_%s"


def test_prepare_dicom_files(tmp_path: Path) -> None:
    first = tmp_path / "a.dcm"
    second = tmp_path / "b.dcm"
    first.write_bytes(b"a")
    second.write_bytes(b"b")
    dest = tmp_path / "series"
    prepare_dicom_dir([first, second], dest)
    assert sorted(path.name for path in dest.iterdir()) == ["a.dcm", "b.dcm"]
    assert not first.exists()


def test_prepare_dicom_zip(tmp_path: Path) -> None:
    archive_path = tmp_path / "series.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("study/IM1.dcm", b"one")
        archive.writestr("study/IM2.dcm", b"two")
    dest = tmp_path / "series"
    prepare_dicom_dir([archive_path], dest)
    assert {path.name for path in dest.iterdir()} == {"IM1.dcm", "IM2.dcm"}
    assert not archive_path.exists()


def test_prepare_rejects_non_dicom_and_traversal(tmp_path: Path) -> None:
    mixed = tmp_path / "mixed.zip"
    with zipfile.ZipFile(mixed, "w") as archive:
        archive.writestr("IM1.dcm", b"one")
        archive.writestr("notes.txt", b"no")
    dest = tmp_path / "series"
    try:
        prepare_dicom_dir([mixed], dest)
        raise AssertionError("expected non-DICOM member to be rejected")
    except ValueError as exc:
        assert "non-DICOM" in str(exc)

    escaped = tmp_path / "escape.zip"
    with zipfile.ZipFile(escaped, "w") as archive:
        archive.writestr("../outside.dcm", b"x")
    try:
        prepare_dicom_dir([escaped], dest)
        raise AssertionError("expected path escape to be rejected")
    except ValueError as exc:
        assert "escapes" in str(exc)


@patch("neuroflow.api.v1.tools.ensure_dcm2niix_available")
@patch("neuroflow.api.v1.tools.launch_mricron_job")
def test_create_mricron_job_api(
    mock_launch: object, _mock_ensure: object, client: TestClient
) -> None:
    mock_launch.return_value = ["dcm2niix", "-f", "%n_%p_%s"]

    response = client.post(
        "/api/v1/tools/mricron/jobs",
        data={
            "workspace": "demo_lab",
            "subject_id": "001",
            "copy_to_anat": "true",
        },
        files=[
            ("files", ("IM1.dcm", b"dicom-a", "application/dicom")),
            ("files", ("IM2.dcm", b"dicom-b", "application/dicom")),
        ],
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["tool_id"] == "mricron"
    mock_launch.assert_called_once()
    assert mock_launch.call_args.kwargs["subject_id"] == "sub-001"
    assert mock_launch.call_args.kwargs["copy_to_anat"] is True
    dicom_dir = mock_launch.call_args.kwargs["dicom_dir"]
    assert {path.name for path in dicom_dir.iterdir()} == {"IM1.dcm", "IM2.dcm"}

    status = client.get(f"/api/v1/tools/mricron/jobs/{body['job_id']}")
    assert status.status_code == 200
    log = client.get(f"/api/v1/tools/mricron/jobs/{body['job_id']}/log")
    assert log.status_code == 200


@patch("neuroflow.api.v1.tools.ensure_dcm2niix_available")
def test_create_mricron_job_rejects_plain_text(_mock_ensure: object, client: TestClient) -> None:
    response = client.post(
        "/api/v1/tools/mricron/jobs",
        data={"workspace": "demo_lab", "subject_id": "sub-001"},
        files=[("files", ("notes.txt", b"nope", "text/plain"))],
    )
    assert response.status_code == 422
    assert "Unsupported" in response.text or "unsupported" in response.text.lower()

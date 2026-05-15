"""BIDS layout helper tests."""

from pathlib import Path

import pytest
from neuroflow.bids.layout import list_subjects, read_dataset_description

SAMPLE_ROOT = Path("data/sample")


@pytest.fixture
def minimal_bids(tmp_path: Path) -> Path:
    root = tmp_path / "bids"
    root.mkdir()
    (root / "dataset_description.json").write_text(
        '{"Name": "Minimal", "BIDSVersion": "1.8.0"}',
        encoding="utf-8",
    )
    anat = root / "sub-01" / "anat"
    anat.mkdir(parents=True)
    (anat / "sub-01_T1w.nii.gz").touch()
    return root


def test_list_subjects(minimal_bids: Path) -> None:
    subjects = list_subjects(minimal_bids)
    assert subjects == ["01"]


def test_read_dataset_description(minimal_bids: Path) -> None:
    assert read_dataset_description(minimal_bids) == "Minimal"


@pytest.mark.skipif(
    not (SAMPLE_ROOT / "dataset_description.json").is_file(),
    reason="Sample BIDS dataset not downloaded",
)
def test_sample_dataset_subjects() -> None:
    subjects = list_subjects(SAMPLE_ROOT.resolve())
    assert len(subjects) > 0

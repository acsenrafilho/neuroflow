"""Tests for runtime path helpers (dev vs frozen)."""

import os
from pathlib import Path
from unittest.mock import patch

from neuroflow.runtime_paths import (
    apply_frozen_defaults,
    bundle_root,
    default_data_root,
    default_datasets_root,
    frontend_dist_dir,
    is_frozen,
    user_data_home,
)


def test_is_frozen_false_in_dev() -> None:
    assert is_frozen() is False


def test_bundle_root_is_repo_root() -> None:
    root = bundle_root()
    assert (root / "neuroflow").is_dir()
    assert (root / "pyproject.toml").is_file()


def test_frontend_dist_dir_under_repo() -> None:
    assert frontend_dist_dir() == bundle_root() / "frontend" / "dist"


def test_default_roots_relative_in_dev() -> None:
    assert default_data_root() == Path("./data/jobs")
    assert default_datasets_root() == Path("./data/datasets")


def test_frozen_defaults(monkeypatch) -> None:
    home = Path("/tmp/neuroflow-home-test")
    with (
        patch("neuroflow.runtime_paths.is_frozen", return_value=True),
        patch("neuroflow.runtime_paths.Path.home", return_value=home),
    ):
        assert default_data_root() == home / ".neuroflow" / "jobs"
        assert default_datasets_root() == home / ".neuroflow" / "datasets"
        assert user_data_home() == home / ".neuroflow"

        monkeypatch.delenv("NEUROFLOW_SERVE_FRONTEND", raising=False)
        monkeypatch.delenv("NEUROFLOW_DATA_ROOT", raising=False)
        monkeypatch.delenv("NEUROFLOW_DATASETS_ROOT", raising=False)
        monkeypatch.delenv("NEUROFLOW_ENV", raising=False)
        apply_frozen_defaults()
        assert os.environ["NEUROFLOW_SERVE_FRONTEND"] == "1"
        assert os.environ["NEUROFLOW_ENV"] == "production"
        assert os.environ["NEUROFLOW_DATA_ROOT"] == str(home / ".neuroflow" / "jobs")

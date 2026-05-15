"""Pytest fixtures."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from neuroflow.api.deps import get_cached_settings
from neuroflow.api.main import app
from neuroflow.config import Settings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    get_cached_settings.cache_clear()
    missing_root = Path("/tmp/neuroflow-test-missing-bids-root")

    def override_settings() -> Settings:
        return Settings(neuroflow_bids_root=missing_root)

    app.dependency_overrides[get_cached_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_cached_settings.cache_clear()


@pytest.fixture
def bids_root(tmp_path: Path) -> Path:
    root = tmp_path / "sample"
    root.mkdir()
    (root / "dataset_description.json").write_text(
        '{"Name": "Test Dataset", "BIDSVersion": "1.8.0"}',
        encoding="utf-8",
    )
    sub = root / "sub-01" / "anat"
    sub.mkdir(parents=True)
    (sub / "sub-01_T1w.nii.gz").touch()
    return root


@pytest.fixture
def client_with_bids(bids_root: Path) -> Generator[TestClient, None, None]:
    get_cached_settings.cache_clear()

    def override_settings() -> Settings:
        return Settings(neuroflow_bids_root=bids_root)

    app.dependency_overrides[get_cached_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_cached_settings.cache_clear()

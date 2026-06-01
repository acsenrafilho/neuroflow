"""Pytest fixtures."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from neuroflow.api.deps import get_cached_settings
from neuroflow.api.main import app
from neuroflow.config import Settings


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "jobs"
    root.mkdir()
    return root


@pytest.fixture
def client(data_root: Path) -> Generator[TestClient, None, None]:
    get_cached_settings.cache_clear()

    def override_settings() -> Settings:
        return Settings(
            neuroflow_data_root=data_root,
            neuroflow_recon_all_bin="/usr/bin/false",
        )

    app.dependency_overrides[get_cached_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_cached_settings.cache_clear()

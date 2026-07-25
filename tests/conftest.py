"""Pytest fixtures."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.api.deps import get_cached_settings
from neuroflow.api.main import app
from neuroflow.config import Settings
from neuroflow.services.job_scheduler import reset_pending_for_tests


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "jobs"
    root.mkdir()
    return root


@pytest.fixture
def datasets_root(tmp_path: Path) -> Path:
    root = tmp_path / "datasets"
    root.mkdir()
    return root


@pytest.fixture
def client(data_root: Path, datasets_root: Path) -> Generator[TestClient, None, None]:
    get_cached_settings.cache_clear()
    reset_pending_for_tests()

    settings = Settings(
        neuroflow_data_root=data_root,
        neuroflow_datasets_root=datasets_root,
        neuroflow_recon_all_bin="/usr/bin/false",
        neuroflow_ram_max_percent=100.0,
        neuroflow_cpu_max_percent=100.0,
        neuroflow_serve_frontend=False,
    )

    def override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_cached_settings] = override_settings
    with (
        patch("neuroflow.api.deps.get_cached_settings", return_value=settings),
        patch("neuroflow.api.main.get_cached_settings", return_value=settings),
        patch(
            "neuroflow.services.job_scheduler.can_start_job",
            return_value=(True, None),
        ),
        patch(
            "neuroflow.services.host_resources.can_start_job",
            return_value=(True, None),
        ),
        TestClient(app) as test_client,
    ):
        yield test_client
    app.dependency_overrides.clear()
    get_cached_settings.cache_clear()
    reset_pending_for_tests()

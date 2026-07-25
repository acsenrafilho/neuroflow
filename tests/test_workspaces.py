"""Workspace list / create / open API and DatasetStore helpers."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from neuroflow.config import Settings
from neuroflow.services.datasets import DatasetStore, sanitize_workspace


def test_list_workspaces_empty(tmp_path: Path) -> None:
    store = DatasetStore(Settings(neuroflow_datasets_root=tmp_path / "datasets"))
    assert store.list_workspaces() == []


def test_create_and_list_workspaces(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    store = DatasetStore(Settings(neuroflow_datasets_root=root))
    created = store.create_workspace("lab_a")
    assert created.name == "lab_a"
    assert created.path.is_dir()
    assert created.subject_count == 0

    store.create_workspace("lab_a")  # idempotent
    store.ensure_subject_tree("lab_a", "001", "anat")
    store.create_workspace("lab_b")

    listed = store.list_workspaces()
    assert [item.name for item in listed] == ["lab_a", "lab_b"]
    assert listed[0].subject_count == 1
    assert listed[1].subject_count == 0


def test_list_skips_derivatives_and_invalid_names(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    store = DatasetStore(Settings(neuroflow_datasets_root=root))
    store.create_workspace("ok_lab")
    (root / "derivatives").mkdir()
    (root / "bad name").mkdir()
    (root / "ok_lab" / "derivatives").mkdir()

    names = [item.name for item in store.list_workspaces()]
    assert names == ["ok_lab"]


def test_resolve_workspace_dir_missing(tmp_path: Path) -> None:
    store = DatasetStore(Settings(neuroflow_datasets_root=tmp_path / "datasets"))
    with pytest.raises(FileNotFoundError):
        store.resolve_workspace_dir("missing")


def test_resolve_workspace_dir_rejects_traversal(tmp_path: Path) -> None:
    store = DatasetStore(Settings(neuroflow_datasets_root=tmp_path / "datasets"))
    with pytest.raises(ValueError):
        sanitize_workspace("../escape")
    with pytest.raises(ValueError):
        store.resolve_workspace_dir("../escape")


def test_workspaces_api_list_create(client: TestClient, datasets_root: Path) -> None:
    empty = client.get("/api/v1/workspaces")
    assert empty.status_code == 200
    assert empty.json() == []

    created = client.post("/api/v1/workspaces", json={"name": "ana silva"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "ana_silva"
    assert body["subject_count"] == 0
    assert Path(body["path"]).is_dir()
    assert Path(body["path"]).parent == datasets_root.resolve()

    listed = client.get("/api/v1/workspaces")
    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()] == ["ana_silva"]


def test_workspaces_api_invalid_name(client: TestClient) -> None:
    response = client.post("/api/v1/workspaces", json={"name": "bad/name"})
    assert response.status_code == 422
    assert "letters" in response.json()["detail"].lower() or "Workspace" in response.json()[
        "detail"
    ]


def test_workspaces_api_open_success(client: TestClient, datasets_root: Path) -> None:
    client.post("/api/v1/workspaces", json={"name": "lab_open"})
    with patch("neuroflow.api.v1.workspaces.open_in_file_manager") as mock_open:
        response = client.post("/api/v1/workspaces/lab_open/open")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_open.assert_called_once()
    opened = mock_open.call_args.args[0]
    assert opened == (datasets_root / "lab_open").resolve()


def test_workspaces_api_open_missing(client: TestClient) -> None:
    response = client.post("/api/v1/workspaces/does_not_exist/open")
    assert response.status_code == 404


def test_open_in_file_manager_calls_xdg_open(tmp_path: Path) -> None:
    from neuroflow.services.reveal_path import open_in_file_manager

    folder = tmp_path / "folder"
    folder.mkdir()
    with (
        patch("neuroflow.services.reveal_path.shutil.which", return_value="/usr/bin/xdg-open"),
        patch("neuroflow.services.reveal_path.subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        mock_run.return_value.stdout = ""
        open_in_file_manager(folder)

    mock_run.assert_called_once()
    args = mock_run.call_args.args[0]
    assert args[0] == "/usr/bin/xdg-open"
    assert args[1] == str(folder.resolve())


def test_open_in_file_manager_missing_opener(tmp_path: Path) -> None:
    from neuroflow.services.reveal_path import open_in_file_manager

    folder = tmp_path / "folder"
    folder.mkdir()
    with patch("neuroflow.services.reveal_path.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="xdg-open"):
            open_in_file_manager(folder)

"""Processing modules API tests."""

from fastapi.testclient import TestClient


def test_list_modules(client: TestClient) -> None:
    response = client.get("/api/v1/modules")
    assert response.status_code == 200
    modules = response.json()
    assert len(modules) >= 4
    fs_modules = [m for m in modules if m["package_id"] == "freesurfer" and not m["coming_soon"]]
    assert len(fs_modules) == 4
    recon_options = {m["recon_options"] for m in fs_modules}
    assert recon_options == {"all", "autorecon1", "autorecon2", "autorecon3"}


def test_modules_alias_under_tools(client: TestClient) -> None:
    response = client.get("/api/v1/tools/modules")
    assert response.status_code == 200
    assert len(response.json()) >= 4

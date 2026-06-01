"""Processing modules API tests."""

from fastapi.testclient import TestClient
from neuroflow.tools.host_probe import TOOL_AVAILABILITY_STATE_KEY, ProbeResult


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


def test_modules_use_cached_host_probe(client: TestClient) -> None:
    client.app.state.tool_availability = {
        "freesurfer": ProbeResult(
            package_id="freesurfer",
            available=True,
            resolved_path="/opt/recon-all",
            detail="ok",
        ),
        "fsl": ProbeResult(
            package_id="fsl",
            available=True,
            resolved_path="/usr/bin/bet",
            detail="ok",
        ),
        "ants": ProbeResult(package_id="ants", available=False, detail="missing"),
    }

    response = client.get("/api/v1/modules")
    assert response.status_code == 200
    modules = response.json()

    fs_modules = [m for m in modules if m["package_id"] == "freesurfer" and not m["coming_soon"]]
    assert len(fs_modules) == 4
    assert all(m["available"] for m in fs_modules)

    fsl = next(m for m in modules if m["id"] == "fsl-placeholder")
    assert fsl["coming_soon"] is True
    assert fsl["available"] is True

    ants = next(m for m in modules if m["id"] == "ants-placeholder")
    assert ants["coming_soon"] is True
    assert ants["available"] is False


def test_host_rescan_updates_cache(client: TestClient) -> None:
    client.app.state.tool_availability = {
        "freesurfer": ProbeResult("freesurfer", available=False, detail="before"),
        "fsl": ProbeResult("fsl", available=False, detail="before"),
        "ants": ProbeResult("ants", available=False, detail="before"),
    }

    response = client.post("/api/v1/host/rescan")
    assert response.status_code == 200
    assert len(response.json()["packages"]) == 3
    assert hasattr(client.app.state, TOOL_AVAILABILITY_STATE_KEY)

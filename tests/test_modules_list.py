"""Processing modules API tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from neuroflow.tools.host_probe import TOOL_AVAILABILITY_STATE_KEY, ProbeResult


def test_list_modules(client: TestClient) -> None:
    response = client.get("/api/v1/modules")
    assert response.status_code == 200
    modules = response.json()
    packages = {m["package_id"] for m in modules}
    assert packages == {"freesurfer", "fsl", "sct"}
    assert not any(m["package_id"] in {"ants", "slicer", "itk"} for m in modules)
    fs_modules = [m for m in modules if m["package_id"] == "freesurfer" and not m["coming_soon"]]
    assert len(fs_modules) == 4
    fsl_modules = [m for m in modules if m["package_id"] == "fsl" and not m["coming_soon"]]
    assert len(fsl_modules) == 15
    sct_modules = [m for m in modules if m["package_id"] == "sct" and not m["coming_soon"]]
    assert len(sct_modules) == 10
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
        "slicer": ProbeResult(
            package_id="slicer",
            available=True,
            resolved_path="/opt/Slicer",
            detail="ok",
        ),
        "itk": ProbeResult(
            package_id="itk",
            available=False,
            detail="no native binaries",
        ),
        "sct": ProbeResult(
            package_id="sct",
            available=False,
            detail="missing",
        ),
    }

    with (
        patch("neuroflow.tools.host_probe.resolve_itk_module_binary", return_value=None),
        patch("neuroflow.tools.host_probe.resolve_executable", return_value=None),
        patch("neuroflow.tools.host_probe.which", return_value=None),
    ):
        response = client.get("/api/v1/modules")
    assert response.status_code == 200
    modules = response.json()

    fs_modules = [m for m in modules if m["package_id"] == "freesurfer" and not m["coming_soon"]]
    assert len(fs_modules) == 4
    assert all(m["available"] for m in fs_modules)

    fsl_bet = next(m for m in modules if m["id"] == "fsl-bet")
    assert fsl_bet["coming_soon"] is False
    assert fsl_bet["available"] is False


def test_host_rescan_updates_cache(client: TestClient) -> None:
    client.app.state.tool_availability = {
        "freesurfer": ProbeResult("freesurfer", available=False, detail="before"),
        "fsl": ProbeResult("fsl", available=False, detail="before"),
        "ants": ProbeResult("ants", available=False, detail="before"),
        "slicer": ProbeResult("slicer", available=False, detail="before"),
        "itk": ProbeResult("itk", available=False, detail="before"),
        "sct": ProbeResult("sct", available=False, detail="before"),
    }

    response = client.post("/api/v1/host/rescan")
    assert response.status_code == 200
    assert len(response.json()["packages"]) == 6
    assert hasattr(client.app.state, TOOL_AVAILABILITY_STATE_KEY)

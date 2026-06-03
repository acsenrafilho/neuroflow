"""Processing modules API tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from neuroflow.tools.host_probe import TOOL_AVAILABILITY_STATE_KEY, ProbeResult


def test_list_modules(client: TestClient) -> None:
    response = client.get("/api/v1/modules")
    assert response.status_code == 200
    modules = response.json()
    assert len(modules) >= 21
    fs_modules = [m for m in modules if m["package_id"] == "freesurfer" and not m["coming_soon"]]
    assert len(fs_modules) == 4
    fsl_modules = [m for m in modules if m["package_id"] == "fsl" and not m["coming_soon"]]
    assert len(fsl_modules) == 15
    recon_options = {m["recon_options"] for m in fs_modules}
    assert recon_options == {"all", "autorecon1", "autorecon2", "autorecon3"}
    slicer_modules = [m for m in modules if m["package_id"] == "slicer" and not m["coming_soon"]]
    assert len(slicer_modules) == 3
    assert {m["id"] for m in slicer_modules} == {
        "slicer-dwi-convert",
        "slicer-dwi-mask",
        "slicer-dwi-to-dti",
    }
    itk_modules = [m for m in modules if m["package_id"] == "itk" and not m["coming_soon"]]
    assert len(itk_modules) == 3
    assert {m["id"] for m in itk_modules} == {
        "itk-diffusion-complexity-mapping",
        "itk-anisotropic-anomalous-diffusion",
        "itk-simple-filter",
    }


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
    }

    with patch("neuroflow.tools.host_probe.resolve_itk_module_binary", return_value=None):
        response = client.get("/api/v1/modules")
    assert response.status_code == 200
    modules = response.json()

    fs_modules = [m for m in modules if m["package_id"] == "freesurfer" and not m["coming_soon"]]
    assert len(fs_modules) == 4
    assert all(m["available"] for m in fs_modules)

    fsl_bet = next(m for m in modules if m["id"] == "fsl-bet")
    assert fsl_bet["coming_soon"] is False
    assert fsl_bet["available"] is True

    ants = next(m for m in modules if m["id"] == "ants-placeholder")
    assert ants["coming_soon"] is True
    assert ants["available"] is False

    slicer_convert = next(m for m in modules if m["id"] == "slicer-dwi-convert")
    assert slicer_convert["available"] is True

    itk_simple = next(m for m in modules if m["id"] == "itk-simple-filter")
    assert itk_simple["available"] is True

    itk_dcm = next(m for m in modules if m["id"] == "itk-diffusion-complexity-mapping")
    assert itk_dcm["available"] is False


def test_host_rescan_updates_cache(client: TestClient) -> None:
    client.app.state.tool_availability = {
        "freesurfer": ProbeResult("freesurfer", available=False, detail="before"),
        "fsl": ProbeResult("fsl", available=False, detail="before"),
        "ants": ProbeResult("ants", available=False, detail="before"),
        "slicer": ProbeResult("slicer", available=False, detail="before"),
        "itk": ProbeResult("itk", available=False, detail="before"),
    }

    response = client.post("/api/v1/host/rescan")
    assert response.status_code == 200
    assert len(response.json()["packages"]) == 5
    assert hasattr(client.app.state, TOOL_AVAILABILITY_STATE_KEY)

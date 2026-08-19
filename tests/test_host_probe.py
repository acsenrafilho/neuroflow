"""Host package probe tests."""

from pathlib import Path
from unittest.mock import patch

import pytest
from neuroflow.config import Settings
from neuroflow.tools.host_probe import (
    ProbeResult,
    module_available,
    probe_ants,
    probe_freesurfer,
    probe_fsl,
    probe_itk,
    probe_sct,
    probe_slicer,
    scan_all_packages,
)
from neuroflow.tools.registry import get_module


def test_probe_freesurfer_when_recon_all_resolved(tmp_path: Path) -> None:
    fake_bin = tmp_path / "recon-all"
    fake_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_bin.chmod(0o755)
    settings = Settings(neuroflow_recon_all_bin=str(fake_bin))
    result = probe_freesurfer(settings)
    assert result.available is True
    assert result.resolved_path == str(fake_bin)


def test_probe_freesurfer_missing() -> None:
    settings = Settings(neuroflow_recon_all_bin="/nonexistent/recon-all")
    with patch("neuroflow.tools.host_probe.resolve_executable", return_value=None):
        result = probe_freesurfer(settings)
    assert result.available is False


def test_probe_fsl_binary_on_path() -> None:
    with patch("neuroflow.tools.host_probe._first_on_path", return_value="/usr/bin/bet"):
        result = probe_fsl()
    assert result.available is True
    assert result.resolved_path == "/usr/bin/bet"


def test_probe_fsl_via_fsldir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FSLDIR", raising=False)
    with patch("neuroflow.tools.host_probe._first_on_path", return_value=None):
        monkeypatch.setenv("FSLDIR", str(tmp_path))
        result = probe_fsl()
    assert result.available is True
    assert result.resolved_path == str(tmp_path)


def test_probe_ants_missing() -> None:
    settings = Settings()
    with (
        patch("neuroflow.tools.base.resolve_executable", return_value=None),
        patch("neuroflow.tools.host_probe._first_on_path", return_value=None),
        patch("neuroflow.tools.base._ants_bin_dir", return_value=None),
    ):
        result = probe_ants(settings)
    assert result.available is False


def test_probe_ants_found_via_resolve() -> None:
    settings = Settings()
    with patch(
        "neuroflow.tools.base.resolve_executable",
        return_value=Path("/usr/bin/antsRegistration"),
    ):
        result = probe_ants(settings)
    assert result.available is True


def test_probe_ants_found_on_path() -> None:
    settings = Settings()
    with (
        patch("neuroflow.tools.base.resolve_executable", return_value=None),
        patch(
            "neuroflow.tools.host_probe._first_on_path",
            return_value="/usr/bin/antsRegistration",
        ),
    ):
        result = probe_ants(settings)
    assert result.available is True


def test_probe_ants_via_antspath(tmp_path: Path) -> None:
    binary = tmp_path / "antsRegistration"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    settings = Settings(neuroflow_antspath=tmp_path)
    with (
        patch("neuroflow.tools.base.resolve_executable", return_value=binary),
        patch("neuroflow.tools.host_probe._first_on_path", return_value=None),
    ):
        result = probe_ants(settings)
    assert result.available is True


def test_probe_slicer_on_path() -> None:
    with patch("neuroflow.tools.host_probe.resolve_executable", return_value=Path("/opt/Slicer")):
        result = probe_slicer(Settings())
    assert result.available is True
    assert result.resolved_path == "/opt/Slicer"


def test_probe_slicer_via_home(tmp_path: Path) -> None:
    slicer_bin = tmp_path / "Slicer"
    slicer_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    slicer_bin.chmod(0o755)
    settings = Settings(neuroflow_slicer_home=tmp_path)
    with (
        patch("neuroflow.tools.host_probe.resolve_executable", return_value=None),
        patch("neuroflow.tools.host_probe._first_on_path", return_value=None),
    ):
        result = probe_slicer(settings)
    assert result.available is True
    assert result.resolved_path == str(slicer_bin)


def test_probe_slicer_missing() -> None:
    with (
        patch("neuroflow.tools.host_probe.resolve_executable", return_value=None),
        patch("neuroflow.tools.host_probe._first_on_path", return_value=None),
    ):
        result = probe_slicer(Settings())
    assert result.available is False


def test_probe_itk_no_config() -> None:
    settings = Settings(neuroflow_itk_binaries_config=None)
    with patch("neuroflow.tools.itk_binaries.itk_binaries_config_path", return_value=None):
        result = probe_itk(settings)
    assert result.available is False
    assert "itk-binaries" in result.detail


def test_probe_itk_with_configured_binary(tmp_path: Path) -> None:
    binary = tmp_path / "dcm"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        f'{{"itk-diffusion-complexity-mapping": "{binary}"}}',
        encoding="utf-8",
    )
    settings = Settings(neuroflow_itk_binaries_config=config_path)
    result = probe_itk(settings)
    assert result.available is True
    assert result.resolved_path == str(binary)


def test_probe_sct_binary_on_path() -> None:
    with patch(
        "neuroflow.tools.host_probe.resolve_executable",
        return_value=Path("/home/user/sct_7.3/bin/sct_version"),
    ):
        result = probe_sct(Settings())
    assert result.available is True
    assert result.resolved_path == "/home/user/sct_7.3/bin/sct_version"


def test_probe_sct_via_sct_dir(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    version_bin = bin_dir / "sct_version"
    version_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    version_bin.chmod(0o755)
    settings = Settings(neuroflow_sct_dir=tmp_path)
    result = probe_sct(settings)
    assert result.available is True
    assert result.resolved_path == str(version_bin)


def test_probe_sct_autodetect_home_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install = tmp_path / "sct_7.3"
    bin_dir = install / "bin"
    bin_dir.mkdir(parents=True)
    version_bin = bin_dir / "sct_version"
    version_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    version_bin.chmod(0o755)
    monkeypatch.delenv("SCT_DIR", raising=False)
    monkeypatch.delenv("NEUROFLOW_SCT_DIR", raising=False)
    with (
        patch("neuroflow.tools.base._default_sct_install_roots", return_value=[install]),
        patch("neuroflow.tools.host_probe._first_on_path", return_value=None),
        patch("neuroflow.tools.base.which", return_value=None),
    ):
        result = probe_sct(Settings())
    assert result.available is True
    assert result.resolved_path == str(version_bin)


def test_probe_sct_missing() -> None:
    with (
        patch("neuroflow.tools.host_probe.resolve_executable", return_value=None),
        patch("neuroflow.tools.host_probe._first_on_path", return_value=None),
        patch("neuroflow.tools.host_probe._sct_root_dir", return_value=None),
    ):
        result = probe_sct(Settings())
    assert result.available is False


def test_module_available_sct_via_sct_dir(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("sct_version", "sct_deepseg"):
        binary = bin_dir / name
        binary.write_text("#!/bin/sh\n", encoding="utf-8")
        binary.chmod(0o755)
    settings = Settings(neuroflow_sct_dir=tmp_path)
    results = {"sct": ProbeResult("sct", True, resolved_path=str(bin_dir / "sct_version"))}
    module = get_module("sct-deepseg")
    assert module is not None
    with patch("neuroflow.tools.host_probe.which", return_value=None):
        assert module_available(results, module, settings) is True


def test_module_available_itk_binary_and_worker(tmp_path: Path) -> None:
    binary = tmp_path / "dcm"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        f'{{"itk-diffusion-complexity-mapping": "{binary}"}}',
        encoding="utf-8",
    )
    settings = Settings(neuroflow_itk_binaries_config=config_path)
    results = {
        "itk": ProbeResult("itk", True, resolved_path=str(binary), detail="ok"),
        "slicer": ProbeResult("slicer", True, resolved_path="/opt/Slicer", detail="ok"),
    }
    dcm = get_module("itk-diffusion-complexity-mapping")
    assert dcm is not None
    assert module_available(results, dcm, settings) is True

    simple = get_module("itk-simple-filter")
    assert simple is not None
    assert module_available(results, simple, settings) is True

    results["slicer"] = ProbeResult("slicer", False, detail="missing")
    assert module_available(results, simple, settings) is False


def test_scan_all_packages_returns_all_ids() -> None:
    settings = Settings()
    with (
        patch("neuroflow.tools.host_probe.probe_freesurfer") as mock_fs,
        patch("neuroflow.tools.host_probe.probe_fsl") as mock_fsl,
        patch("neuroflow.tools.host_probe.probe_ants") as mock_ants,
        patch("neuroflow.tools.host_probe.probe_slicer") as mock_slicer,
        patch("neuroflow.tools.host_probe.probe_itk") as mock_itk,
        patch("neuroflow.tools.host_probe.probe_sct") as mock_sct,
    ):
        mock_fs.return_value = ProbeResult("freesurfer", False, detail="x")
        mock_fsl.return_value = ProbeResult("fsl", False, detail="y")
        mock_ants.return_value = ProbeResult("ants", False, detail="z")
        mock_slicer.return_value = ProbeResult("slicer", False, detail="w")
        mock_itk.return_value = ProbeResult("itk", False, detail="v")
        mock_sct.return_value = ProbeResult("sct", False, detail="u")
        results = scan_all_packages(settings)
    assert set(results.keys()) == {"freesurfer", "fsl", "ants", "slicer", "itk", "sct"}

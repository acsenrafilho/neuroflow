"""Host package probe tests."""

from pathlib import Path
from unittest.mock import patch

import pytest
from neuroflow.config import Settings
from neuroflow.tools.host_probe import (
    probe_ants,
    probe_freesurfer,
    probe_fsl,
    scan_all_packages,
)


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
    with patch("neuroflow.tools.host_probe._first_on_path", return_value=None):
        result = probe_ants()
    assert result.available is False


def test_probe_ants_found() -> None:
    with patch(
        "neuroflow.tools.host_probe._first_on_path",
        return_value="/usr/bin/antsRegistration",
    ):
        result = probe_ants()
    assert result.available is True


def test_scan_all_packages_returns_all_ids() -> None:
    settings = Settings()
    with (
        patch("neuroflow.tools.host_probe.probe_freesurfer") as mock_fs,
        patch("neuroflow.tools.host_probe.probe_fsl") as mock_fsl,
        patch("neuroflow.tools.host_probe.probe_ants") as mock_ants,
    ):
        from neuroflow.tools.host_probe import ProbeResult

        mock_fs.return_value = ProbeResult("freesurfer", False, detail="x")
        mock_fsl.return_value = ProbeResult("fsl", False, detail="y")
        mock_ants.return_value = ProbeResult("ants", False, detail="z")
        results = scan_all_packages(settings)
    assert set(results.keys()) == {"freesurfer", "fsl", "ants"}

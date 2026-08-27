"""Tests for Windows release zip assembly (Phase 3 layout)."""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_ASM_PATH = _ROOT / "packaging" / "assemble_windows_release.py"
_SPEC = importlib.util.spec_from_file_location("assemble_windows_release", _ASM_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_asm = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_asm)

AssembleError = _asm.AssembleError
assemble_windows_release = _asm.assemble_windows_release
stage_windows_release = _asm.stage_windows_release
validate_linux_onedir = _asm.validate_linux_onedir


def _make_linux_onedir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "neuroflow").write_bytes(b"\x7fELF")
    internal = root / "_internal"
    internal.mkdir()
    (internal / "marker").write_text("linux", encoding="utf-8")
    return root


def _make_launcher_onedir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "NeuroFlow.exe").write_bytes(b"MZ")
    internal = root / "_internal"
    internal.mkdir()
    (internal / "marker").write_text("win", encoding="utf-8")
    return root


def _readme(path: Path) -> Path:
    path.write_text("NeuroFlow for Windows\n", encoding="utf-8")
    return path


class TestValidateLinuxOnedir:
    def test_ok(self, tmp_path: Path) -> None:
        validate_linux_onedir(_make_linux_onedir(tmp_path / "linux"))

    def test_missing_elf(self, tmp_path: Path) -> None:
        bad = tmp_path / "linux"
        bad.mkdir()
        (bad / "_internal").mkdir()
        with pytest.raises(AssembleError, match="neuroflow"):
            validate_linux_onedir(bad)

    def test_rejects_wrapping_folder_without_flat_elf(self, tmp_path: Path) -> None:
        """A tree with only nested neuroflow/neuroflow must fail validation."""
        wrapped = tmp_path / "linux"
        inner = wrapped / "neuroflow"
        inner.mkdir(parents=True)
        (inner / "neuroflow").write_bytes(b"\x7fELF")
        (inner / "_internal").mkdir()
        with pytest.raises(AssembleError, match="nested"):
            validate_linux_onedir(wrapped)


class TestAssembleWindowsRelease:
    def test_zip_layout(self, tmp_path: Path) -> None:
        linux = _make_linux_onedir(tmp_path / "linux-onedir")
        launcher = _make_launcher_onedir(tmp_path / "NeuroFlow")
        readme = _readme(tmp_path / "README-WINDOWS.txt")
        out = tmp_path / "release"

        zip_path = assemble_windows_release(
            linux_onedir=linux,
            launcher_onedir=launcher,
            version="0.0.1",
            output_dir=out,
            readme=readme,
        )

        assert zip_path.name == "neuroflow-0.0.1-windows-x86_64.zip"
        assert zip_path.is_file()

        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())

        assert "NeuroFlow.exe" in names
        assert "README-WINDOWS.txt" in names
        assert "linux-payload/neuroflow" in names
        assert any(n.startswith("linux-payload/_internal/") for n in names)
        assert any(n.startswith("_internal/") for n in names)
        # Must not nest ELF as linux-payload/neuroflow/neuroflow
        assert "linux-payload/neuroflow/neuroflow" not in names
        # Flat zip root — no wrapping NeuroFlow/ folder for the exe
        assert "NeuroFlow/NeuroFlow.exe" not in names

    def test_stage_copies_payload_flat(self, tmp_path: Path) -> None:
        linux = _make_linux_onedir(tmp_path / "linux-onedir")
        launcher = _make_launcher_onedir(tmp_path / "NeuroFlow")
        readme = _readme(tmp_path / "README-WINDOWS.txt")
        staging = tmp_path / "staging"

        stage_windows_release(
            linux_onedir=linux,
            launcher_onedir=launcher,
            readme=readme,
            staging=staging,
        )

        assert (staging / "NeuroFlow.exe").is_file()
        assert (staging / "linux-payload" / "neuroflow").is_file()
        assert (staging / "linux-payload" / "_internal" / "marker").is_file()
        assert not (staging / "linux-payload" / "neuroflow").is_dir()

    def test_missing_launcher_exe(self, tmp_path: Path) -> None:
        linux = _make_linux_onedir(tmp_path / "linux-onedir")
        launcher = tmp_path / "NeuroFlow"
        launcher.mkdir()
        (launcher / "_internal").mkdir()
        readme = _readme(tmp_path / "README-WINDOWS.txt")

        with pytest.raises(AssembleError, match="NeuroFlow.exe"):
            assemble_windows_release(
                linux_onedir=linux,
                launcher_onedir=launcher,
                version="0.0.1",
                output_dir=tmp_path / "out",
                readme=readme,
            )


class TestWindowsLauncherSpec:
    def test_spec_targets_launcher_not_portal(self) -> None:
        spec = (_ROOT / "packaging" / "windows_launcher.spec").read_text(encoding="utf-8")
        assert "windows_launcher_app.py" in spec
        assert "packaged_app.py" not in spec
        assert 'collect_all("uvicorn")' not in spec
        assert 'name="NeuroFlow"' in spec
        assert "frontend/dist" not in spec

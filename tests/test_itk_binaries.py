"""ITK binaries JSON configuration tests."""

import json
from pathlib import Path

from neuroflow.config import Settings
from neuroflow.tools.itk_binaries import (
    ITK_NATIVE_MODULE_IDS,
    load_itk_binaries_config,
    resolve_itk_module_binary,
)


def test_load_itk_binaries_config_valid(tmp_path: Path) -> None:
    binary = tmp_path / "dcm"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        json.dumps({"itk-diffusion-complexity-mapping": str(binary)}),
        encoding="utf-8",
    )
    settings = Settings(neuroflow_itk_binaries_config=config_path)
    loaded = load_itk_binaries_config(settings)
    assert loaded["itk-diffusion-complexity-mapping"] == binary.resolve()


def test_load_itk_binaries_rejects_relative_path(tmp_path: Path) -> None:
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        json.dumps({"itk-diffusion-complexity-mapping": "relative/binary"}),
        encoding="utf-8",
    )
    settings = Settings(neuroflow_itk_binaries_config=config_path)
    assert load_itk_binaries_config(settings) == {}


def test_load_itk_binaries_rejects_non_executable(tmp_path: Path) -> None:
    binary = tmp_path / "dcm"
    binary.write_text("not executable\n", encoding="utf-8")
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        json.dumps({"itk-diffusion-complexity-mapping": str(binary)}),
        encoding="utf-8",
    )
    settings = Settings(neuroflow_itk_binaries_config=config_path)
    assert load_itk_binaries_config(settings) == {}


def test_resolve_itk_module_binary(tmp_path: Path) -> None:
    binary = tmp_path / "aad"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    config_path = tmp_path / "itk-binaries.json"
    config_path.write_text(
        json.dumps({"itk-anisotropic-anomalous-diffusion": str(binary)}),
        encoding="utf-8",
    )
    settings = Settings(neuroflow_itk_binaries_config=config_path)
    resolved = resolve_itk_module_binary(settings, "itk-anisotropic-anomalous-diffusion")
    assert resolved == binary.resolve()
    assert resolve_itk_module_binary(settings, "itk-diffusion-complexity-mapping") is None


def test_native_module_ids_cover_registry_keys() -> None:
    assert "itk-diffusion-complexity-mapping" in ITK_NATIVE_MODULE_IDS
    assert "itk-anisotropic-anomalous-diffusion" in ITK_NATIVE_MODULE_IDS

"""Load ITK module binary paths from a host-specific JSON configuration file."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path

from neuroflow.config import Settings

logger = logging.getLogger(__name__)

ITK_NATIVE_MODULE_IDS: frozenset[str] = frozenset(
    {
        "itk-diffusion-complexity-mapping",
        "itk-anisotropic-anomalous-diffusion",
    }
)

DEFAULT_CONFIG_RELATIVE = Path("config/itk-binaries.json")


def itk_binaries_config_path(settings: Settings) -> Path | None:
    """Return the JSON config path from settings or the default file if it exists."""
    if settings.neuroflow_itk_binaries_config is not None:
        return settings.neuroflow_itk_binaries_config.resolve()
    if DEFAULT_CONFIG_RELATIVE.is_file():
        return DEFAULT_CONFIG_RELATIVE.resolve()
    return None


def _validate_binary_path(module_id: str, raw: str) -> Path | None:
    path = Path(raw)
    if not path.is_absolute():
        logger.warning(
            "ITK config: %s must be an absolute path (got %r)", module_id, raw
        )
        return None
    if not path.is_file():
        logger.warning("ITK config: %s path does not exist: %s", module_id, path)
        return None
    if not os.access(path, os.X_OK):
        logger.warning("ITK config: %s path is not executable: %s", module_id, path)
        return None
    return path


def _parse_config_file(config_path: Path) -> dict[str, Path]:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ITK config: failed to read %s: %s", config_path, exc)
        return {}

    if not isinstance(data, dict):
        logger.warning("ITK config: root must be a JSON object in %s", config_path)
        return {}

    resolved: dict[str, Path] = {}
    for module_id, value in data.items():
        if not isinstance(module_id, str) or not isinstance(value, str):
            logger.warning(
                "ITK config: skip invalid entry %r -> %r", module_id, value
            )
            continue
        binary = _validate_binary_path(module_id, value.strip())
        if binary is not None:
            resolved[module_id] = binary
    return resolved


@lru_cache(maxsize=8)
def _load_cached(config_path_str: str, mtime_ns: int) -> dict[str, Path]:
    return _parse_config_file(Path(config_path_str))


def load_itk_binaries_config(settings: Settings) -> dict[str, Path]:
    """Return module_id -> executable path for entries in the ITK binaries JSON file."""
    config_path = itk_binaries_config_path(settings)
    if config_path is None:
        return {}
    try:
        mtime_ns = config_path.stat().st_mtime_ns
    except OSError:
        return {}
    return _load_cached(str(config_path), mtime_ns)


def resolve_itk_module_binary(settings: Settings, module_id: str) -> Path | None:
    """Return the configured executable for a native ITK module, if valid."""
    return load_itk_binaries_config(settings).get(module_id)


def count_configured_native_binaries(settings: Settings) -> tuple[int, int]:
    """Return (configured_count, total_native_modules) for package probe messaging."""
    config = load_itk_binaries_config(settings)
    configured = sum(1 for mid in ITK_NATIVE_MODULE_IDS if mid in config)
    return configured, len(ITK_NATIVE_MODULE_IDS)

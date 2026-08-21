"""Resolve filesystem paths for development vs PyInstaller frozen builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True when running inside a PyInstaller (or similar) bundle."""
    return bool(getattr(sys, "frozen", False)) and hasattr(sys, "_MEIPASS")


def bundle_root() -> Path:
    """Root that contains bundled assets (``frontend/dist``, etc.).

    In a frozen build this is ``sys._MEIPASS``. In development it is the
    repository root (parent of the ``neuroflow`` package).
    """
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def frontend_dist_dir() -> Path:
    """Directory with built UI pages and assets."""
    return bundle_root() / "frontend" / "dist"


def user_data_home() -> Path:
    """Writable base directory for job/dataset data in frozen builds."""
    return Path.home() / ".neuroflow"


def default_data_root() -> Path:
    if is_frozen():
        return user_data_home() / "jobs"
    return Path("./data/jobs")


def default_datasets_root() -> Path:
    if is_frozen():
        return user_data_home() / "datasets"
    return Path("./data/datasets")


def apply_frozen_defaults() -> None:
    """Set env defaults for packaged runs when the user has not overridden them.

    Safe to call from the PyInstaller entrypoint before Settings are loaded.
    No-op when not frozen.
    """
    if not is_frozen():
        return

    os.environ.setdefault("NEUROFLOW_SERVE_FRONTEND", "1")
    os.environ.setdefault("NEUROFLOW_ENV", "production")
    os.environ.setdefault("NEUROFLOW_DATA_ROOT", str(default_data_root()))
    os.environ.setdefault("NEUROFLOW_DATASETS_ROOT", str(default_datasets_root()))

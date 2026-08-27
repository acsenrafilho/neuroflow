#!/usr/bin/env python3
"""Assemble the Windows release zip: launcher onedir + Linux portal payload.

Stdlib only — runnable on Linux CI without Wine. Flattens the zip root so
NeuroFlow.exe sits next to linux-payload/ (Phase 2 payload.resolve contract).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

_README_NAME = "README-WINDOWS.txt"
_PAYLOAD_DIR = "linux-payload"
_EXE_NAME = "NeuroFlow.exe"
_ARCH_LABEL = "x86_64"


class AssembleError(Exception):
    """Raised when the Windows release layout cannot be assembled."""


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise AssembleError(f"{label} not found: {path}")


def _require_dir(path: Path, label: str) -> None:
    if not path.is_dir():
        raise AssembleError(f"{label} not found: {path}")


def validate_linux_onedir(linux_onedir: Path) -> None:
    """Ensure ``linux_onedir`` is a flat PyInstaller portal onedir."""
    _require_dir(linux_onedir, "Linux onedir")
    elf = linux_onedir / "neuroflow"
    internal = linux_onedir / "_internal"
    if elf.is_dir():
        nested = elf / "neuroflow"
        raise AssembleError(
            f"Linux onedir looks nested ({nested}); pass the inner onedir contents, "
            "not a wrapping neuroflow/ folder."
        )
    _require_file(elf, "Linux portal executable")
    _require_dir(internal, "Linux portal _internal")


def validate_launcher_onedir(launcher_onedir: Path) -> None:
    """Ensure ``launcher_onedir`` is a flat PyInstaller launcher onedir."""
    _require_dir(launcher_onedir, "Launcher onedir")
    exe = launcher_onedir / _EXE_NAME
    internal = launcher_onedir / "_internal"
    _require_file(exe, "NeuroFlow.exe")
    _require_dir(internal, "Launcher _internal")


def validate_staging(staging: Path) -> None:
    """Assert the staged Windows zip root matches the frozen layout."""
    _require_file(staging / _EXE_NAME, "Staged NeuroFlow.exe")
    _require_dir(staging / "_internal", "Staged launcher _internal")
    payload = staging / _PAYLOAD_DIR
    _require_dir(payload, "Staged linux-payload")
    _require_file(payload / "neuroflow", "Staged linux-payload/neuroflow")
    _require_dir(payload / "_internal", "Staged linux-payload/_internal")
    _require_file(staging / _README_NAME, f"Staged {_README_NAME}")
    # Must not wrap as linux-payload/neuroflow/neuroflow
    nested = payload / "neuroflow"
    if nested.is_dir():
        raise AssembleError(
            f"linux-payload must contain the ELF at linux-payload/neuroflow, "
            f"not a nested directory at {nested}"
        )


def stage_windows_release(
    *,
    linux_onedir: Path,
    launcher_onedir: Path,
    readme: Path,
    staging: Path,
) -> Path:
    """Copy launcher + Linux payload + README into ``staging`` (flat root)."""
    validate_linux_onedir(linux_onedir)
    validate_launcher_onedir(launcher_onedir)
    _require_file(readme, _README_NAME)

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    shutil.copy2(launcher_onedir / _EXE_NAME, staging / _EXE_NAME)
    shutil.copytree(launcher_onedir / "_internal", staging / "_internal")

    payload_dest = staging / _PAYLOAD_DIR
    payload_dest.mkdir()
    for item in linux_onedir.iterdir():
        dest = payload_dest / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    shutil.copy2(readme, staging / _README_NAME)
    validate_staging(staging)
    return staging


def zip_staging(staging: Path, zip_path: Path) -> Path:
    """Write ``staging`` contents to ``zip_path`` (flat archive root)."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(staging).as_posix())
    return zip_path


def assemble_windows_release(
    *,
    linux_onedir: Path,
    launcher_onedir: Path,
    version: str,
    output_dir: Path,
    readme: Path | None = None,
    staging: Path | None = None,
) -> Path:
    """Build ``neuroflow-<ver>-windows-x86_64.zip`` and return its path."""
    root = Path(__file__).resolve().parent
    readme_path = readme if readme is not None else root / _README_NAME
    out = output_dir.resolve()
    stage = staging if staging is not None else out / "_windows_staging"
    zip_name = f"neuroflow-{version}-windows-{_ARCH_LABEL}.zip"
    zip_path = out / zip_name

    stage_windows_release(
        linux_onedir=linux_onedir.resolve(),
        launcher_onedir=launcher_onedir.resolve(),
        readme=readme_path.resolve(),
        staging=stage,
    )
    try:
        return zip_staging(stage, zip_path)
    finally:
        if staging is None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble NeuroFlow Windows release zip (launcher + linux-payload).",
    )
    parser.add_argument(
        "--linux-onedir",
        type=Path,
        required=True,
        help="Path to the Linux portal onedir (contains neuroflow + _internal/)",
    )
    parser.add_argument(
        "--launcher-onedir",
        type=Path,
        required=True,
        help="Path to the PyInstaller launcher onedir (dist/NeuroFlow)",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version string for the zip name (e.g. 0.0.1)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for neuroflow-<ver>-windows-x86_64.zip",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=None,
        help=f"Path to {_README_NAME} (default: packaging/{_README_NAME})",
    )
    args = parser.parse_args(argv)

    try:
        zip_path = assemble_windows_release(
            linux_onedir=args.linux_onedir,
            launcher_onedir=args.launcher_onedir,
            version=args.version,
            output_dir=args.output_dir,
            readme=args.readme,
        )
    except AssembleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Built {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

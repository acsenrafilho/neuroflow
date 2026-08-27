# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir spec for the Windows WSL launcher (not the portal)."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
root = Path(SPECPATH).resolve().parent

# Launcher only: Rich console + windows_launcher package. No frontend, uvicorn, or FastAPI.
hiddenimports = [
    "rich",
    "rich.console",
]
hiddenimports += collect_submodules("neuroflow.windows_launcher")

a = Analysis(
    [str(root / "neuroflow" / "windows_launcher_app.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "uvicorn",
        "fastapi",
        "multipart",
        "starlette",
        "pydantic",
        "pydantic_settings",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NeuroFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NeuroFlow",
)

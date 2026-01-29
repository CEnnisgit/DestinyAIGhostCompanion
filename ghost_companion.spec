# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for bundling the Ghost Companion launcher."""

from pathlib import Path

block_cipher = None

# PyInstaller does not always set __file__ in spec execution context on Windows,
# so fall back to cwd when missing.
REPO_ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
FRONTEND_BUILD_DIR = REPO_ROOT / "frontend" / "build"


a = Analysis(
    ['launch.py'],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=[
        # Package the built frontend under 'frontend/build' so server.py
        # can find it regardless of frozen/runtime layout.
        (str(FRONTEND_BUILD_DIR), 'frontend/build'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GhostCompanionLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
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
    name='GhostCompanionLauncher',
)

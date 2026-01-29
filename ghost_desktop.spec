# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for bundling the Ghost Companion desktop app."""

from pathlib import Path

block_cipher = None

# PyInstaller may not set __file__ when executing the spec; fall back to cwd.
REPO_ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
FRONTEND_BUILD_DIR = REPO_ROOT / "frontend" / "build"

from PyInstaller.utils.hooks import collect_submodules

# Exclude heavy optional libs to keep the desktop build small.
EXCLUDES = [
    'faster_whisper', 'ctranslate2', 'onnxruntime', 'av', 'tokenizers',
    'torch', 'torchvision', 'torchtext', 'tensorflow', 'jax', 'jaxlib',
]

# If you later want to include local STT, remove the excludes above.

datas_list = []
if FRONTEND_BUILD_DIR.exists():
    datas_list.append((str(FRONTEND_BUILD_DIR), 'frontend/build'))

a = Analysis(
    ['ghost/desktop.py'],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas_list,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
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
    name='GhostCompanion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
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
    name='GhostCompanion',
)

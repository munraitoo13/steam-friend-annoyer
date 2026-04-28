# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building Windows executable.
Built with PyInstaller 6.0+

Run: pyinstaller build/pyinstaller.spec
Output: dist/SteamFriendAnnoyer.exe
"""

from pathlib import Path

block_cipher = None

# PyInstaller executes spec files without defining __file__.
# The build script runs with the project root as the current working directory.
project_root = Path.cwd()

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PySide6",
        "steam",
        "requests",
        "cryptography",
        "win32crypt",
        "win32api",
        "win32con",
        "pywintypes",
        "pythoncom",
        "pywin32",
        "steam.protobufs.steammessages_friendmessages_pb2",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name="SteamFriendAnnoyer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,  # Support for code signing - can be set to certificate name
    entitlements_file=None,
    icon=None,  # Can be set to path/to/icon.ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SteamFriendAnnoyer",
)

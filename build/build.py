#!/usr/bin/env python3
"""Build script for creating Windows executable."""

import importlib.util
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def build():
    """Build the application using PyInstaller."""
    if sys.platform != "win32":
        print("This build script generates a Windows .exe and must run on Windows.")
        print("Current platform:", sys.platform)
        print("Use a Windows machine (or Windows CI) to run this build.")
        sys.exit(1)

    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller is not installed in the current environment.")
        print("Install dev dependencies first, then run build again:")
        print("  uv sync --extra dev")
        print("or")
        print("  uv sync --all-extras")
        sys.exit(1)

    spec_file = PROJECT_ROOT / "build" / "pyinstaller.spec"

    print(f"Building with PyInstaller spec: {spec_file}")
    print(f"Output directory: {PROJECT_ROOT / 'dist'}")

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_file)],
        cwd=str(PROJECT_ROOT),
    )

    if result.returncode == 0:
        exe_path = (
            PROJECT_ROOT / "dist" / "SteamFriendAnnoyer" / "SteamFriendAnnoyer.exe"
        )
        print("\n✓ Build successful!")
        print(f"Executable: {exe_path}")
        print(f"\nTo run: {exe_path}")
    else:
        print("\n✗ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    build()

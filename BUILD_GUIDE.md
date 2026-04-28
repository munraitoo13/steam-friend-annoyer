# Build Guide - Windows Only

This document explains how to build the Windows executable. **Note: PyInstaller must be run on Windows to create a Windows executable.**

## ⚠️ Important

- This project runs on **Linux for development**
- The executable (.exe) must be **built on Windows**
- All other functionality (UI, Steam API, etc.) is cross-platform

## Prerequisites

You must be on **Windows** with:

- Python 3.12 or later
- Git (to clone the repository)

## Building the Executable on Windows

### Step 1: Clone and Setup

```bash
git clone https://github.com/munraitoo13/steam-friend-annoyer.git
cd steam-friend-annoyer
```

### Step 2: Install Dependencies (including dev)

```bash
# Using uv (recommended)
uv sync --all-extras

# Or using pip
pip install -e ".[dev]"
```

### Step 3: Build

```bash
# Using the build script
python build/build.py

# Or directly with PyInstaller
pyinstaller build/pyinstaller.spec
```

### Step 4: Find Your Executable

```
dist/SteamFriendAnnoyer/SteamFriendAnnoyer.exe
```

You can now:

- Run it directly: double-click `SteamFriendAnnoyer.exe`
- Share it with others
- Distribute via GitHub releases
- Create an installer (optional)

## Customization Before Building

### Add Custom Icon

1. Create or prepare an icon file (`.ico` format)
2. Edit `build/pyinstaller.spec`:
   ```python
   icon="path/to/your/icon.ico",
   ```
3. Rebuild

### Add Code Signing

1. Obtain a code signing certificate
2. Edit `build/pyinstaller.spec`:
   ```python
   codesign_identity="Your Certificate Name",
   ```
3. Rebuild

## Troubleshooting Build Issues

### PyInstaller Not Found

```bash
pip install pyinstaller>=6.0.0
```

### Build Fails

- Check that all dependencies installed: `pip list | grep -i required-package`
- Clear build cache: `rm -rf build/ dist/`
- Rebuild: `python build/build.py`

### Missing Modules in Executable

The `pyinstaller.spec` has `hiddenimports` for known modules. If something is missing:

1. Add module to `hiddenimports` in `build/pyinstaller.spec`
2. Rebuild

## Distribution

### GitHub Release

1. Build the executable on Windows
2. Create a new release: https://github.com/munraitoo13/steam-friend-annoyer/releases
3. Upload `SteamFriendAnnoyer.exe`
4. Users can download and run directly

### Auto-Update

The application checks for updates automatically. Set the release tag as `v1.0.0`, `v1.1.0`, etc., and the app will:

- Detect new versions
- Prompt user to download
- Download and replace executable
- Restart the application

## For Cross-Platform Development

If you want to develop on Linux/Mac:

1. Install dependencies: `uv sync`
2. Run the app: `uv run python main.py`
3. Code normally
4. When ready to build for Windows, move to a Windows machine or use CI/CD

## CI/CD Automation

The repository includes a GitHub Actions workflow at `.github/workflows/build-windows.yml`.

What it does:

- Builds on every push to `main`
- Uploads the `.exe` as a workflow artifact
- Builds and publishes a GitHub Release asset when you push a version tag like `v1.0.1`

Typical release flow:

```bash
git tag v1.0.1
git push origin v1.0.1
```

That triggers the workflow, builds the Windows executable, and attaches it to the GitHub Release so users can download it from the Releases page.

If you only push to `main`, the build still runs and the executable is downloadable from the Actions run artifact, but it will not become a permanent release download until you push a version tag.

## Summary

| Task              | Command                 | Platform         |
| ----------------- | ----------------------- | ---------------- |
| Install for dev   | `uv sync`               | Any              |
| Run from source   | `uv run python main.py` | Any              |
| Build executable  | `python build/build.py` | **Windows only** |
| Install for users | Download .exe           | Windows          |

---

**For Linux/Mac users developing the code:** Build on Windows or use CI/CD automation.

**For Windows users:** Follow the steps above to build your own executable.

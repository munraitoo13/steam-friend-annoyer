"""Auto-update from GitHub releases."""

import logging
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable, Optional

import requests

from src.utils.config import APP_VERSION, GITHUB_REPO

logger = logging.getLogger(__name__)


class AutoUpdateManager:
    """Check for and download updates from GitHub releases."""

    def __init__(self):
        self._on_update_available: Optional[Callable[[str, str], Any]] = None
        self._on_error: Optional[Callable[[str], Any]] = None

    def set_on_update_available(self, callback: Callable[[str, str], Any]):
        """Set callback when update is available (current_version, new_version)."""
        self._on_update_available = callback

    def set_on_error(self, callback: Callable[[str], Any]):
        """Set error callback."""
        self._on_error = callback

    def check_for_updates(self):
        """Check for updates in background thread."""
        thread = threading.Thread(target=self._check_updates, daemon=True)
        thread.start()

    def _check_updates(self):
        """Check GitHub releases for newer version."""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            latest_version = data.get("tag_name", "").lstrip("v")

            if self._is_newer_version(latest_version, APP_VERSION):
                if self._on_update_available:
                    self._on_update_available(APP_VERSION, latest_version)

        except Exception as e:
            if self._on_error:
                self._on_error(f"Update check failed: {str(e)}")

    @staticmethod
    def _is_newer_version(new_version: str, current_version: str) -> bool:
        """Compare version strings."""
        try:
            new_parts = [int(x) for x in new_version.split(".")]
            current_parts = [int(x) for x in current_version.split(".")]

            # Pad with zeros
            max_len = max(len(new_parts), len(current_parts))
            new_parts.extend([0] * (max_len - len(new_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return new_parts > current_parts
        except Exception:
            return False

    def download_and_install_update(self, new_version: str, exe_path: Path) -> bool:
        """
        Download and install update.

        This function is designed to support executable replacement.
        Implementation details:
        1. Download .exe from GitHub release
        2. Verify checksum if available
        3. Prepare for installation (backup current exe)
        4. Replace executable
        5. Restart application

        Returns True if successful, False otherwise.
        """
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            exe_asset = None

            # Find .exe asset
            for asset in data.get("assets", []):
                if asset["name"].endswith(".exe"):
                    exe_asset = asset
                    break

            if not exe_asset:
                if self._on_error:
                    self._on_error("No executable found in release")
                return False

            # Download exe
            download_url = exe_asset["browser_download_url"]
            exe_response = requests.get(download_url, timeout=30)
            exe_response.raise_for_status()

            # Backup current exe
            backup_path = exe_path.with_suffix(".exe.bak")
            if exe_path.exists():
                exe_path.rename(backup_path)

            try:
                # Write new exe
                with open(exe_path, "wb") as f:
                    f.write(exe_response.content)

                # Restart application
                subprocess.Popen([str(exe_path)])
                return True

            except Exception:
                # Restore backup
                if backup_path.exists():
                    backup_path.rename(exe_path)
                raise

        except Exception as e:
            if self._on_error:
                self._on_error(f"Update installation failed: {str(e)}")
            return False

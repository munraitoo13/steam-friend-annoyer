"""Configuration and path management."""

import os
from pathlib import Path


def get_app_data_dir() -> Path:
    """Get the application data directory (%APPDATA%/SteamFriendAnnoyer/)."""
    appdata = os.getenv("APPDATA")
    if not appdata:
        # Fallback for non-Windows
        appdata = str(Path.home() / "AppData" / "Roaming")

    app_dir = Path(appdata) / "SteamFriendAnnoyer"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_friends_file() -> Path:
    """Get friends.json path."""
    return get_app_data_dir() / "friends.json"


def get_messages_file() -> Path:
    """Get messages.json path."""
    return get_app_data_dir() / "messages.json"


def get_config_file() -> Path:
    """Get config.json path."""
    return get_app_data_dir() / "config.json"


def get_session_file() -> Path:
    """Get encrypted session file path."""
    return get_app_data_dir() / "session.enc"


APP_VERSION = "1.0.0"
GITHUB_REPO = "munraitoo13/steam-friend-annoyer"

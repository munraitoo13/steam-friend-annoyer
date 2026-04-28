"""Persistence layer for managing application data."""

import json
import threading
from typing import Any, Dict, List, Optional

from src.utils.config import (
    get_app_data_dir,
    get_config_file,
    get_friends_file,
    get_messages_file,
    get_session_file,
)
from src.utils.encryption import decrypt_json, encrypt_json
from src.utils.validators import (
    is_valid_message,
    is_valid_steam_id,
    normalize_message,
    parse_steam_id,
)


class StorageManager:
    """Thread-safe manager for all persistent data."""

    def __init__(self):
        self._lock = threading.RLock()
        self._friends: List[int] = []
        self._messages: List[str] = []
        self._config: Dict[str, Any] = {}
        self._session: Optional[Dict[str, Any]] = None
        self._load_all()

    def _load_all(self):
        """Load all data from disk."""
        with self._lock:
            self._load_friends()
            self._load_messages()
            self._load_config()
            self._load_session()

    def _load_friends(self):
        """Load friends list from friends.json."""
        friends_file = get_friends_file()
        if friends_file.exists():
            try:
                with open(friends_file, "r") as f:
                    data = json.load(f)
                    self._friends = [
                        int(fid)
                        for fid in data.get("friends", [])
                        if is_valid_steam_id(int(fid))
                    ]
            except Exception:
                self._friends = []
        else:
            self._friends = self._get_default_friends()
            self._save_friends()

    def _load_messages(self):
        """Load messages list from messages.json."""
        messages_file = get_messages_file()
        if messages_file.exists():
            try:
                with open(messages_file, "r") as f:
                    data = json.load(f)
                    self._messages = [
                        m for m in data.get("messages", []) if is_valid_message(m)
                    ]
            except Exception:
                self._messages = []
        else:
            self._messages = self._get_default_messages()
            self._save_messages()

    def _load_config(self):
        """Load config from config.json."""
        config_file = get_config_file()
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    self._config = json.load(f)
            except Exception:
                self._config = {}
        else:
            self._config = {
                "start_with_windows": False,
                "start_minimized": False,
            }
            self._save_config()

    def _load_session(self):
        """Load encrypted session data."""
        session_file = get_session_file()
        if session_file.exists():
            try:
                with open(session_file, "rb") as f:
                    encrypted = f.read()
                    self._session = decrypt_json(encrypted)
            except Exception:
                self._session = None
        else:
            self._session = None

    def _save_friends(self):
        """Save friends list to disk."""
        friends_file = get_friends_file()
        with open(friends_file, "w") as f:
            json.dump({"friends": self._friends}, f, indent=2)

    def _save_messages(self):
        """Save messages list to disk."""
        messages_file = get_messages_file()
        with open(messages_file, "w") as f:
            json.dump({"messages": self._messages}, f, indent=2)

    def _save_config(self):
        """Save config to disk."""
        config_file = get_config_file()
        with open(config_file, "w") as f:
            json.dump(self._config, f, indent=2)

    def _save_session(self):
        """Save encrypted session data."""
        session_file = get_session_file()
        if self._session:
            encrypted = encrypt_json(self._session)
            with open(session_file, "wb") as f:
                f.write(encrypted)
        else:
            session_file.unlink(missing_ok=True)

    @staticmethod
    def _get_default_friends() -> List[int]:
        """Get default friends list for first run."""
        return []

    @staticmethod
    def _get_default_messages() -> List[str]:
        """Get default messages for first run."""
        return [
            "pode fechar",
            "sai do jogo",
            "vc tá viciado demais",
            "larga esse jogo",
        ]

    # --- Public API: Friends ---

    def get_friends(self) -> List[int]:
        """Get list of monitored friends."""
        with self._lock:
            return self._friends.copy()

    def add_friend(self, input_str: str) -> bool:
        """
        Add a friend by SteamID64 or profile URL.
        Returns True if added, False if invalid or duplicate.
        """
        steam_id = parse_steam_id(input_str)
        if steam_id is None or not is_valid_steam_id(steam_id):
            return False

        with self._lock:
            if steam_id not in self._friends:
                self._friends.append(steam_id)
                self._save_friends()
                return True
            return False

    def remove_friend(self, steam_id: int) -> bool:
        """Remove a friend. Returns True if removed."""
        with self._lock:
            if steam_id in self._friends:
                self._friends.remove(steam_id)
                self._save_friends()
                return True
            return False

    # --- Public API: Messages ---

    def get_messages(self) -> List[str]:
        """Get list of messages."""
        with self._lock:
            return self._messages.copy()

    def add_message(self, message: str) -> bool:
        """Add a message. Returns True if added, False if invalid."""
        normalized = normalize_message(message)
        if not is_valid_message(normalized):
            return False

        with self._lock:
            if normalized not in self._messages:
                self._messages.append(normalized)
                self._save_messages()
                return True
            return False

    def remove_message(self, message: str) -> bool:
        """Remove a message. Returns True if removed."""
        with self._lock:
            normalized = normalize_message(message)
            if normalized in self._messages:
                self._messages.remove(normalized)
                self._save_messages()
                return True
            return False

    # --- Public API: Config ---

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        with self._lock:
            return self._config.get(key, default)

    def set_config(self, key: str, value: Any):
        """Set a config value and save."""
        with self._lock:
            self._config[key] = value
            self._save_config()

    # --- Public API: Session ---

    def get_session(self) -> Optional[Dict[str, Any]]:
        """Get stored session data."""
        with self._lock:
            return self._session.copy() if self._session else None

    def set_session(self, session: Dict[str, Any]):
        """Store encrypted session data."""
        with self._lock:
            self._session = session
            self._save_session()

    def clear_session(self):
        """Clear session (removes login cache)."""
        with self._lock:
            self._session = None
            self._save_session()

    def clear_all_data(self):
        """Clear everything (full reset)."""
        with self._lock:
            self._friends = []
            self._messages = self._get_default_messages()
            self._config = {
                "start_with_windows": False,
                "start_minimized": False,
            }
            self._session = None

            self._save_friends()
            self._save_messages()
            self._save_config()
            self._save_session()

            # Delete data directory
            app_dir = get_app_data_dir()
            try:
                for file in app_dir.glob("*"):
                    if file.is_file():
                        file.unlink()
            except Exception:
                pass

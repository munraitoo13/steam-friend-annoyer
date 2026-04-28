"""Application controller - main orchestration."""

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from src.persistence.storage import StorageManager
from src.steam_service.client import SteamService
from src.system_integration.auto_update import AutoUpdateManager
from src.system_integration.notifications import send_notification
from src.system_integration.tray import TrayIcon
from src.ui.main_window import MainWindow
from src.utils.config import get_app_data_dir

logger = logging.getLogger(__name__)


class _UiEventBridge(QObject):
    """Qt signal bridge to move background callbacks onto the main thread."""

    steam_connected = Signal()
    steam_disconnected = Signal()
    steam_friend_state_changed = Signal(object, object)
    steam_message_sent = Signal(object, str)
    steam_error = Signal(str)
    update_available = Signal(str, str)
    update_error = Signal(str)


class ApplicationController:
    """Orchestrates the application components."""

    def __init__(self):
        self.storage = StorageManager()
        self.steam_service = SteamService(self.storage)
        self.ui = MainWindow()
        self.tray = TrayIcon()
        self.update_manager = AutoUpdateManager()
        self._bridge = _UiEventBridge()

        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._guard_retry_in_progress = False

        self._setup_callbacks()
        self._populate_ui()

    def _setup_callbacks(self):
        """Connect all callbacks."""
        # UI callbacks
        self.ui.set_on_add_friend(self._on_add_friend)
        self.ui.set_on_remove_friend(self._on_remove_friend)
        self.ui.set_on_add_message(self._on_add_message)
        self.ui.set_on_remove_message(self._on_remove_message)
        self.ui.set_on_run(self._on_run_clicked)
        self.ui.set_on_stop(self._on_stop_clicked)
        self.ui.set_on_start_with_windows(self._on_start_with_windows)
        self.ui.set_on_start_minimized(self._on_start_minimized)
        self.ui.set_on_clear_session(self._on_clear_session)
        self.ui.set_on_clear_all(self._on_clear_all)
        self.ui.set_on_open_logs(self._on_open_logs)

        # Tray callbacks
        self.tray.set_on_start(self._on_run_clicked)
        self.tray.set_on_stop(self._on_stop_clicked)
        self.tray.set_on_open(self._on_tray_open)
        self.tray.set_on_exit(self._on_tray_exit)

        # Steam service callbacks
        self._bridge.steam_connected.connect(self._on_steam_connected)
        self._bridge.steam_disconnected.connect(self._on_steam_disconnected)
        self._bridge.steam_friend_state_changed.connect(self._on_friend_state_changed)
        self._bridge.steam_message_sent.connect(self._on_message_sent)
        self._bridge.steam_error.connect(self._on_steam_error)

        self.steam_service.set_on_connected(lambda: self._bridge.steam_connected.emit())
        self.steam_service.set_on_disconnected(
            lambda: self._bridge.steam_disconnected.emit()
        )
        self.steam_service.set_on_friend_state_changed(
            lambda friend_id, game_id: self._bridge.steam_friend_state_changed.emit(
                friend_id, game_id
            )
        )
        self.steam_service.set_on_message_sent(
            lambda friend_id, message: self._bridge.steam_message_sent.emit(
                friend_id, message
            )
        )
        self.steam_service.set_on_error(
            lambda message: self._bridge.steam_error.emit(message)
        )

        # Auto-update callbacks
        self._bridge.update_available.connect(self._on_update_available)
        self._bridge.update_error.connect(self._on_update_error)
        self.update_manager.set_on_update_available(
            lambda current_version, new_version: self._bridge.update_available.emit(
                current_version, new_version
            )
        )
        self.update_manager.set_on_error(
            lambda message: self._bridge.update_error.emit(message)
        )

    def _populate_ui(self):
        """Load and display stored data."""
        friends = self.storage.get_friends()
        self.ui.populate_friends(friends)

        messages = self.storage.get_messages()
        self.ui.populate_messages(messages)

        # Load config
        start_with_windows = self.storage.get_config("start_with_windows", False)
        start_minimized = self.storage.get_config("start_minimized", False)

        self.ui.settings_widget.set_start_with_windows(start_with_windows)
        self.ui.settings_widget.set_start_minimized(start_minimized)

    def show(self):
        """Show main window."""
        logger.debug("Showing main window")
        self.ui.show()
        self.tray.show()
        self.tray.update_menu(False)
        self.update_manager.check_for_updates()

    def run(self):
        """Run the application."""
        logger.debug("Running application controller")
        self.ui.show()
        self.tray.show()
        self.tray.update_menu(False)

    # --- UI Callbacks ---

    def _on_add_friend(self, input_str: str):
        """Add friend from UI input."""
        if self.storage.add_friend(input_str):
            friends = self.storage.get_friends()
            self.ui.populate_friends(friends)
        else:
            self.ui.show_error(
                "Invalid Friend", "Could not parse Steam ID or profile URL"
            )

    def _on_remove_friend(self, friend_id: int):
        """Remove friend."""
        if self.storage.remove_friend(friend_id):
            friends = self.storage.get_friends()
            self.ui.populate_friends(friends)

    def _on_add_message(self, message: str):
        """Add message from UI input."""
        if self.storage.add_message(message):
            messages = self.storage.get_messages()
            self.ui.populate_messages(messages)
        else:
            self.ui.show_error("Invalid Message", "Message cannot be empty")

    def _on_remove_message(self, message: str):
        """Remove message."""
        if self.storage.remove_message(message):
            messages = self.storage.get_messages()
            self.ui.populate_messages(messages)

    def _on_run_clicked(self):
        """Start monitoring."""
        logger.debug("Run requested")

        if not self.storage.get_friends():
            self.ui.show_error(
                "No Friends", "Please add at least one friend to monitor"
            )
            return

        if not self.storage.get_messages():
            self.ui.show_error("No Messages", "Please add at least one message")
            return

        # Try to load existing session
        session = self.storage.get_session()
        guard_code: Optional[str] = None
        self._guard_retry_in_progress = False

        # Reuse stored credentials when available.
        if session and session.get("username") and session.get("password"):
            self._username = session.get("username")
            self._password = session.get("password")
            logger.debug("Using stored credentials for %s", self._username)
        else:
            login_result = self.ui.show_login_dialog()
            if not login_result:
                logger.debug("Login dialog cancelled")
                return

            self._username, self._password, guard_code = login_result
            logger.debug(
                "Received credentials from login dialog for %s", self._username
            )

        # Start Steam service
        logger.debug(
            "Starting Steam service: friends=%d messages=%d session_cached=%s guard_code=%s",
            len(self.storage.get_friends()),
            len(self.storage.get_messages()),
            bool(session),
            bool(guard_code),
        )
        if not self.steam_service.start(
            self._username,
            self._password,
            session,
            guard_code,
        ):
            logger.error("Steam service refused to start")
            self.ui.show_error("Error", "Failed to start Steam client")
            return

        self.ui.set_running(True)
        self.tray.update_menu(True)
        self.ui.set_status("running")

    def _on_stop_clicked(self):
        """Stop monitoring."""
        logger.debug("Stop requested")
        self.steam_service.stop()
        self.ui.set_running(False)
        self.tray.update_menu(False)
        self.ui.set_status("disconnected")

    def _on_start_with_windows(self, checked: bool):
        """Set start with Windows."""
        self.storage.set_config("start_with_windows", checked)
        # TODO: Set registry/startup folder

    def _on_start_minimized(self, checked: bool):
        """Set start minimized."""
        self.storage.set_config("start_minimized", checked)

    def _on_clear_session(self):
        """Clear login session."""
        logger.debug("Clearing stored session")
        self.steam_service.stop()
        self.storage.clear_session()
        self.ui.show_info("Session Cleared", "Login cache has been removed")

    def _on_clear_all(self):
        """Clear all data."""
        logger.debug("Clearing all application data")
        self.steam_service.stop()
        self.storage.clear_all_data()
        self.ui.show_info("Data Cleared", "All data has been reset")
        # Reload UI
        self._populate_ui()

    def _on_open_logs(self):
        """Open the app data folder for log inspection."""
        app_dir = get_app_data_dir()
        logger.debug("Opening app data directory: %s", app_dir)

        try:
            if os.name == "nt":
                os.startfile(app_dir)
                return

            QDesktopServices.openUrl(QUrl.fromLocalFile(str(app_dir)))
        except Exception as exc:
            logger.error("Failed to open app data directory: %s", exc)
            self.ui.show_error(
                "Open Logs Failed",
                f"Could not open {app_dir}. You can still inspect app.log manually.",
            )

    def _on_tray_open(self):
        """Show window from tray."""
        self.ui.showNormal()
        self.ui.activateWindow()

    def _on_tray_exit(self):
        """Exit application."""
        self.steam_service.stop()
        QApplication.quit()

    # --- Steam Service Callbacks ---

    def _on_steam_connected(self):
        """Called when Steam client connects."""
        logger.debug("Steam client connected")
        self.ui.set_status("running")
        self.tray.set_status("Running")

    def _on_steam_disconnected(self):
        """Called when Steam client disconnects."""
        logger.debug("Steam client disconnected")
        if self.steam_service.is_running():
            self.ui.set_status("error")
            self.tray.set_status("Disconnected")
        else:
            self.ui.set_status("disconnected")
            self.tray.set_status("Stopped")

    def _on_friend_state_changed(self, friend_id: int, game_id: Optional[int]):
        """Called when friend's game state changes."""
        if game_id is None:
            logger.info(f"Friend {friend_id} stopped playing")
        else:
            logger.info(f"Friend {friend_id} started playing game {game_id}")

    def _on_message_sent(self, friend_id: int, message: str):
        """Called when message is sent."""
        logger.info(f"Message sent to {friend_id}: {message}")
        send_notification(
            "Message Sent",
            f"Sent to {friend_id}: {message[:50]}...",
        )

    def _on_steam_error(self, error_message: str):
        """Called on Steam error."""
        logger.error(f"Steam error: {error_message}")

        # Retry once with Steam Guard code when login explicitly requires it.
        if self._is_guard_code_required_error(error_message):
            if self._guard_retry_in_progress:
                self.ui.show_error(
                    "Steam Guard Failed",
                    "Steam Guard code was rejected or login still failed.",
                )
                self.ui.set_status("error")
                return

            code = self.ui.show_2fa_dialog()
            if code and self._username and self._password:
                self._guard_retry_in_progress = True
                if self.steam_service.start(
                    self._username,
                    self._password,
                    self.storage.get_session(),
                    code,
                ):
                    self.ui.set_running(True)
                    self.tray.update_menu(True)
                    self.ui.set_status("running")
                    return

        self.ui.set_status("error")

    @staticmethod
    def _is_guard_code_required_error(error_message: str) -> bool:
        """Return True when login failed because Steam Guard code is required."""
        markers = (
            "AccountLoginDeniedNeedTwoFactor",
            "AccountLogonDenied",
            "InvalidLoginAuthCode",
            "TwoFactorCodeMismatch",
            "Login failed: 85",
            "Login failed: 63",
            "Login failed: 65",
            "Login failed: 88",
        )
        return any(marker in error_message for marker in markers)

    # --- Update Callbacks ---

    def _on_update_available(self, current_version: str, new_version: str):
        """Called when update is available."""
        if self.ui.show_question(
            "Update Available",
            f"New version {new_version} is available. Download now?",
        ):
            if self.update_manager.download_and_install_update(
                new_version,
                Path(QApplication.applicationFilePath()),
            ):
                self.ui.show_info("Update Complete", "The application will restart")
                QApplication.quit()

    def _on_update_error(self, error_message: str):
        """Called on update error."""
        logger.error(f"Update error: {error_message}")

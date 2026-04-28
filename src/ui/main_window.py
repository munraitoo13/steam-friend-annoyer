"""Main application window."""

import logging
from typing import Callable, Optional

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets import ControlWidget, ListWithInputWidget, SettingsWidget

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """Login dialog for Steam credentials."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Steam Login")
        self.setModal(True)
        self.setMinimumWidth(300)

        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.two_fa_code: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Username
        layout.addWidget(QLabel("Steam Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(QLabel("Steam Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Optional Steam Guard code (mobile or email)
        layout.addWidget(QLabel("Steam Guard Code (optional):"))
        self.guard_code_input = QLineEdit()
        self.guard_code_input.setPlaceholderText(
            "Only needed when Steam Guard is enabled"
        )
        layout.addWidget(self.guard_code_input)

        # Buttons
        button_layout = QHBoxLayout()
        login_button = QPushButton("Login")
        login_button.clicked.connect(self._on_login)
        button_layout.addWidget(login_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return

        self.username = username
        self.password = password
        self.two_fa_code = self.guard_code_input.text().strip() or None
        self.accept()

    def prompt_2fa(self) -> Optional[str]:
        """Prompt for 2FA code."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Steam Guard")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter Steam Guard code:"))

        code_input = QLineEdit()
        layout.addWidget(code_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            return code_input.text().strip()
        return None


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Friend Annoyer")
        self.setMinimumSize(QSize(600, 700))

        # Callbacks
        self._on_add_friend: Optional[Callable[[str], None]] = None
        self._on_remove_friend: Optional[Callable[[int], None]] = None
        self._on_add_message: Optional[Callable[[str], None]] = None
        self._on_remove_message: Optional[Callable[[str], None]] = None
        self._on_run: Optional[Callable] = None
        self._on_stop: Optional[Callable] = None
        self._on_start_with_windows: Optional[Callable[[bool], None]] = None
        self._on_start_minimized: Optional[Callable[[bool], None]] = None
        self._on_clear_session: Optional[Callable] = None
        self._on_clear_all: Optional[Callable] = None

        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Tab widget
        tabs = QTabWidget()

        # Friends tab
        self.friends_widget = ListWithInputWidget("Enter SteamID64 or profile URL")
        self.friends_widget.set_on_item_added(self._on_friend_added)
        self.friends_widget.set_on_item_removed(self._on_friend_removed)
        tabs.addTab(self.friends_widget, "Friends")

        # Messages tab
        self.messages_widget = ListWithInputWidget("Enter message text")
        self.messages_widget.set_on_item_added(self._on_message_added)
        self.messages_widget.set_on_item_removed(self._on_message_removed)
        tabs.addTab(self.messages_widget, "Messages")

        # Settings tab
        self.settings_widget = SettingsWidget()
        self.settings_widget.set_on_start_with_windows(
            self._on_start_with_windows_changed
        )
        self.settings_widget.set_on_start_minimized(self._on_start_minimized_changed)
        self.settings_widget.set_on_clear_session(self._on_clear_session_clicked)
        self.settings_widget.set_on_clear_all(self._on_clear_all_clicked)
        tabs.addTab(self.settings_widget, "Settings")

        main_layout.addWidget(tabs)

        # Control section
        self.control_widget = ControlWidget()
        self.control_widget.set_on_run(self._on_run_clicked)
        self.control_widget.set_on_stop(self._on_stop_clicked)
        main_layout.addWidget(self.control_widget)

        central_widget.setLayout(main_layout)

    def set_on_add_friend(self, callback: Callable[[str], None]):
        self._on_add_friend = callback

    def set_on_remove_friend(self, callback: Callable[[int], None]):
        self._on_remove_friend = callback

    def set_on_add_message(self, callback: Callable[[str], None]):
        self._on_add_message = callback

    def set_on_remove_message(self, callback: Callable[[str], None]):
        self._on_remove_message = callback

    def set_on_run(self, callback: Callable):
        self._on_run = callback

    def set_on_stop(self, callback: Callable):
        self._on_stop = callback

    def set_on_start_with_windows(self, callback: Callable[[bool], None]):
        self._on_start_with_windows = callback

    def set_on_start_minimized(self, callback: Callable[[bool], None]):
        self._on_start_minimized = callback

    def set_on_clear_session(self, callback: Callable):
        self._on_clear_session = callback

    def set_on_clear_all(self, callback: Callable):
        self._on_clear_all = callback

    def show_login_dialog(self) -> Optional[tuple]:
        """Show login dialog. Returns (username, password, guard_code) or None if cancelled."""
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.Accepted:
            return (dialog.username, dialog.password, dialog.two_fa_code)
        return None

    def show_2fa_dialog(self) -> Optional[str]:
        """Show 2FA prompt. Returns code or None if cancelled."""
        dialog = LoginDialog(self)
        return dialog.prompt_2fa()

    def populate_friends(self, friends: list):
        """Populate friends list."""
        self.friends_widget.clear_items()
        for friend_id in friends:
            self.friends_widget.add_item(str(friend_id))

    def populate_messages(self, messages: list):
        """Populate messages list."""
        self.messages_widget.clear_items()
        for message in messages:
            self.messages_widget.add_item(message)

    def set_running(self, is_running: bool):
        """Update UI for running state."""
        self.control_widget.set_running(is_running)

    def set_status(self, status: str):
        """Set status indicator."""
        self.control_widget.set_status(status)

    def show_error(self, title: str, message: str):
        """Show error dialog."""
        QMessageBox.critical(self, title, message)

    def show_info(self, title: str, message: str):
        """Show info dialog."""
        QMessageBox.information(self, title, message)

    def show_question(self, title: str, message: str) -> bool:
        """Show question dialog. Returns True if Yes, False if No."""
        return (
            QMessageBox.question(
                self,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        )

    def _on_friend_added(self, text: str):
        if self._on_add_friend:
            self._on_add_friend(text)

    def _on_friend_removed(self, text: str):
        try:
            friend_id = int(text)
            if self._on_remove_friend:
                self._on_remove_friend(friend_id)
        except ValueError:
            pass

    def _on_message_added(self, text: str):
        if self._on_add_message:
            self._on_add_message(text)

    def _on_message_removed(self, text: str):
        if self._on_remove_message:
            self._on_remove_message(text)

    def _on_run_clicked(self):
        if self._on_run:
            self._on_run()

    def _on_stop_clicked(self):
        if self._on_stop:
            self._on_stop()

    def _on_start_with_windows_changed(self, checked: bool):
        if self._on_start_with_windows:
            self._on_start_with_windows(checked)

    def _on_start_minimized_changed(self, checked: bool):
        if self._on_start_minimized:
            self._on_start_minimized(checked)

    def _on_clear_session_clicked(self):
        if (
            QMessageBox.question(
                self,
                "Clear Session",
                "This will remove your stored login. You'll need to log in again.",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            if self._on_clear_session:
                self._on_clear_session()

    def _on_clear_all_clicked(self):
        if (
            QMessageBox.question(
                self,
                "Clear All Data",
                "This will permanently delete all settings, friends, messages, and login data.\nAre you sure?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            if self._on_clear_all:
                self._on_clear_all()

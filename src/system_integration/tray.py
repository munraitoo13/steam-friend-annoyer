"""System tray integration."""

from typing import Callable, Optional

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class TrayIcon:
    """System tray icon with menu."""

    def __init__(self, icon_path: Optional[str] = None):
        self._tray_icon = QSystemTrayIcon()
        self._menu = QMenu()
        self._is_available = QSystemTrayIcon.isSystemTrayAvailable()

        # Set icon
        if icon_path:
            self._tray_icon.setIcon(QIcon(icon_path))
        else:
            app = QApplication.instance()
            if app is not None:
                fallback_icon = app.style().standardIcon(QStyle.SP_ComputerIcon)
                self._tray_icon.setIcon(fallback_icon)

        self._tray_icon.setContextMenu(self._menu)

        # Callbacks
        self._on_start: Optional[Callable] = None
        self._on_stop: Optional[Callable] = None
        self._on_open: Optional[Callable] = None
        self._on_exit: Optional[Callable] = None

    def set_on_start(self, callback: Callable):
        """Set start callback."""
        self._on_start = callback

    def set_on_stop(self, callback: Callable):
        """Set stop callback."""
        self._on_stop = callback

    def set_on_open(self, callback: Callable):
        """Set open window callback."""
        self._on_open = callback

    def set_on_exit(self, callback: Callable):
        """Set exit callback."""
        self._on_exit = callback

    def show(self):
        """Show tray icon."""
        if self._is_available:
            self._tray_icon.show()

    def hide(self):
        """Hide tray icon."""
        if self._is_available:
            self._tray_icon.hide()

    def set_status(self, status: str):
        """Update tray icon tooltip."""
        if self._is_available:
            self._tray_icon.setToolTip(f"Steam Friend Annoyer - {status}")

    def update_menu(self, is_running: bool):
        """Update tray menu based on running state."""
        if not self._is_available:
            return

        self._menu.clear()

        if is_running:
            stop_action = QAction("Stop", self._menu)
            stop_action.triggered.connect(self._on_stop_clicked)
            self._menu.addAction(stop_action)
        else:
            start_action = QAction("Start", self._menu)
            start_action.triggered.connect(self._on_start_clicked)
            self._menu.addAction(start_action)

        self._menu.addSeparator()

        open_action = QAction("Open", self._menu)
        open_action.triggered.connect(self._on_open_clicked)
        self._menu.addAction(open_action)

        self._menu.addSeparator()

        exit_action = QAction("Exit", self._menu)
        exit_action.triggered.connect(self._on_exit_clicked)
        self._menu.addAction(exit_action)

    def _on_start_clicked(self):
        if self._on_start:
            self._on_start()

    def _on_stop_clicked(self):
        if self._on_stop:
            self._on_stop()

    def _on_open_clicked(self):
        if self._on_open:
            self._on_open()

    def _on_exit_clicked(self):
        if self._on_exit:
            self._on_exit()

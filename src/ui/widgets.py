"""Reusable UI widgets."""

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ListWithInputWidget(QWidget):
    """Widget combining list, input field, and add/remove buttons."""

    def __init__(self, placeholder: str = "Enter item", parent=None):
        super().__init__(parent)
        self.placeholder = placeholder

        # Callbacks
        self._on_item_added: Optional[Callable[[str], None]] = None
        self._on_item_removed: Optional[Callable[[str], None]] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Input section
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.placeholder)
        self.input_field.returnPressed.connect(self._on_add_clicked)
        input_layout.addWidget(self.input_field)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._on_add_clicked)
        input_layout.addWidget(self.add_button)

        layout.addLayout(input_layout)

        # List section
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

    def set_on_item_added(self, callback: Callable[[str], None]):
        """Set callback when item is added."""
        self._on_item_added = callback

    def set_on_item_removed(self, callback: Callable[[str], None]):
        """Set callback when item is removed."""
        self._on_item_removed = callback

    def add_item(self, text: str):
        """Add item to list."""
        item = QListWidgetItem()
        item.setText(text)
        item.setData(Qt.UserRole, text)  # Store original value
        self.list_widget.addItem(item)

    def remove_item(self, text: str):
        """Remove item from list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == text:
                self.list_widget.takeItem(i)
                break

    def clear_items(self):
        """Clear all items."""
        self.list_widget.clear()

    def get_items(self):
        """Get all items as list."""
        items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            items.append(item.data(Qt.UserRole))
        return items

    def _on_add_clicked(self):
        text = self.input_field.text().strip()
        if text and self._on_item_added:
            self._on_item_added(text)
            self.input_field.clear()

    def _on_item_double_clicked(self, item: QListWidgetItem):
        text = item.data(Qt.UserRole)
        if text and self._on_item_removed:
            self._on_item_removed(text)
            self.list_widget.takeItem(self.list_widget.row(item))


class StatusIndicatorWidget(QWidget):
    """Status indicator with label."""

    STATUS_COLORS = {
        "connected": "#28a745",  # Green
        "disconnected": "#6c757d",  # Gray
        "running": "#007bff",  # Blue
        "error": "#dc3545",  # Red
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout()

        self.status_label = QLabel("Disconnected")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.set_status("disconnected")

    def set_status(self, status: str):
        """Set status: connected, disconnected, running, error."""
        color = self.STATUS_COLORS.get(status, "#6c757d")
        self.status_label.setText(status.title())
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")


class ControlWidget(QWidget):
    """Control section with Run/Stop button and status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on_run: Optional[Callable] = None
        self._on_stop: Optional[Callable] = None
        self._is_running = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_indicator = StatusIndicatorWidget()
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Control button
        self.control_button = QPushButton("Run")
        self.control_button.setMinimumHeight(40)
        self.control_button.clicked.connect(self._on_button_clicked)
        layout.addWidget(self.control_button)

        self.setLayout(layout)

    def set_on_run(self, callback: Callable):
        """Set run callback."""
        self._on_run = callback

    def set_on_stop(self, callback: Callable):
        """Set stop callback."""
        self._on_stop = callback

    def set_running(self, is_running: bool):
        """Update button state."""
        self._is_running = is_running
        self.control_button.setText("Stop" if is_running else "Run")
        self.control_button.setStyleSheet(
            "background-color: #dc3545;" if is_running else "background-color: #28a745;"
        )

    def set_status(self, status: str):
        """Set status indicator."""
        self.status_indicator.set_status(status)

    def _on_button_clicked(self):
        if self._is_running:
            if self._on_stop:
                self._on_stop()
        else:
            if self._on_run:
                self._on_run()


class SettingsWidget(QWidget):
    """Settings section."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on_start_with_windows: Optional[Callable[[bool], None]] = None
        self._on_start_minimized: Optional[Callable[[bool], None]] = None
        self._on_clear_session: Optional[Callable] = None
        self._on_clear_all: Optional[Callable] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Checkboxes
        self.start_with_windows = QCheckBox("Start with Windows")
        self.start_with_windows.stateChanged.connect(self._on_start_windows_changed)
        layout.addWidget(self.start_with_windows)

        self.start_minimized = QCheckBox("Start minimized")
        self.start_minimized.stateChanged.connect(self._on_start_minimized_changed)
        layout.addWidget(self.start_minimized)

        layout.addSpacing(10)

        # Buttons
        self.clear_session_button = QPushButton("Clear Session (Remove Login Cache)")
        self.clear_session_button.clicked.connect(self._on_clear_session_clicked)
        layout.addWidget(self.clear_session_button)

        self.clear_all_button = QPushButton("Clear All Data (Full Reset)")
        self.clear_all_button.setStyleSheet("background-color: #dc3545;")
        self.clear_all_button.clicked.connect(self._on_clear_all_clicked)
        layout.addWidget(self.clear_all_button)

        layout.addStretch()
        self.setLayout(layout)

    def set_on_start_with_windows(self, callback: Callable[[bool], None]):
        self._on_start_with_windows = callback

    def set_on_start_minimized(self, callback: Callable[[bool], None]):
        self._on_start_minimized = callback

    def set_on_clear_session(self, callback: Callable):
        self._on_clear_session = callback

    def set_on_clear_all(self, callback: Callable):
        self._on_clear_all = callback

    def set_start_with_windows(self, checked: bool):
        self.start_with_windows.setChecked(checked)

    def set_start_minimized(self, checked: bool):
        self.start_minimized.setChecked(checked)

    def _on_start_windows_changed(self):
        if self._on_start_with_windows:
            self._on_start_with_windows(self.start_with_windows.isChecked())

    def _on_start_minimized_changed(self):
        if self._on_start_minimized:
            self._on_start_minimized(self.start_minimized.isChecked())

    def _on_clear_session_clicked(self):
        if self._on_clear_session:
            self._on_clear_session()

    def _on_clear_all_clicked(self):
        if self._on_clear_all:
            self._on_clear_all()


class DiagnosticsWidget(QWidget):
    """Live diagnostics and log viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on_open_logs: Optional[Callable] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Live Logs")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Runtime logs will appear here.")
        self.log_view.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.log_view)

        button_layout = QHBoxLayout()

        self.copy_button = QPushButton("Copy Logs")
        self.copy_button.clicked.connect(self._copy_logs)
        button_layout.addWidget(self.copy_button)

        self.clear_button = QPushButton("Clear View")
        self.clear_button.clicked.connect(self.log_view.clear)
        button_layout.addWidget(self.clear_button)

        self.open_logs_button = QPushButton("Open Log Folder")
        self.open_logs_button.clicked.connect(self._on_open_logs_clicked)
        button_layout.addWidget(self.open_logs_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def set_on_open_logs(self, callback: Callable):
        """Set callback for opening the log folder."""
        self._on_open_logs = callback

    def append_log_entry(self, text: str):
        """Append a log line to the viewer."""
        self.log_view.appendPlainText(text)

        lines = self.log_view.toPlainText().splitlines()
        if len(lines) > 1000:
            self.log_view.setPlainText("\n".join(lines[-1000:]))

        self.log_view.moveCursor(QTextCursor.End)

    def _copy_logs(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_view.toPlainText())

    def _on_open_logs_clicked(self):
        if self._on_open_logs:
            self._on_open_logs()

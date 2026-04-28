"""Application entry point."""

import logging
import sys

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from src.app_controller import ApplicationController
from src.utils.config import get_app_data_dir


class QtLogEmitter(QObject):
    """Bridge Python logging into the Qt UI thread."""

    message = Signal(str)


class QtLogHandler(logging.Handler):
    """Logging handler that forwards formatted records to Qt."""

    def __init__(self, emitter: QtLogEmitter):
        super().__init__(level=logging.DEBUG)
        self._emitter = emitter

    def emit(self, record: logging.LogRecord):
        try:
            self._emitter.message.emit(self.format(record))
        except Exception:
            self.handleError(record)


# Setup logging
log_dir = get_app_data_dir()
log_file = log_dir / "app.log"
log_emitter = QtLogEmitter()

file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

gui_handler = QtLogHandler(log_emitter)
gui_handler.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        file_handler,
        stream_handler,
        gui_handler,
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger.info("Application starting...")
    logger.debug("App data directory: %s", log_dir)

    app = QApplication(sys.argv)
    app.setApplicationName("Steam Friend Annoyer")
    app.setApplicationVersion("1.0.0")

    # Create and run application
    controller = ApplicationController()
    log_emitter.message.connect(controller.ui.append_log_entry)
    logger.debug("Connected live log viewer")
    controller.run()

    logger.info("Application running...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

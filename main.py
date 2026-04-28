"""Application entry point."""

import logging
import sys

from PySide6.QtWidgets import QApplication

from src.app_controller import ApplicationController
from src.utils.config import get_app_data_dir

# Setup logging
log_dir = get_app_data_dir()
log_file = log_dir / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger.info("Application starting...")

    app = QApplication(sys.argv)
    app.setApplicationName("Steam Friend Annoyer")
    app.setApplicationVersion("1.0.0")

    # Create and run application
    controller = ApplicationController()
    controller.run()

    logger.info("Application running...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

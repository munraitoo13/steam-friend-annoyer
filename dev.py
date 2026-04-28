"""Development and build utilities."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def install_dev_dependencies():
    """Install development dependencies."""
    print("Installing development dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
        cwd=str(PROJECT_ROOT),
    )


def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=str(PROJECT_ROOT),
    )


def run_dev():
    """Run application in development mode."""
    print("Running application in development mode...")
    subprocess.run(
        [sys.executable, "main.py"],
        cwd=str(PROJECT_ROOT),
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["install", "install-dev", "run"],
        help="Command to run",
    )
    args = parser.parse_args()

    if args.command == "install":
        install_dependencies()
    elif args.command == "install-dev":
        install_dev_dependencies()
    elif args.command == "run":
        run_dev()

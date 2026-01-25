from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import ClassVar

from pythonjsonlogger.json import JsonFormatter

from rubiks_cube.configuration import LOG_LEVEL
from rubiks_cube.configuration.paths import LOGS_PATH


class ColorFormatter(logging.Formatter):
    COLOR_MAP: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[1;31m",
    }
    RESET: ClassVar[str] = "\033[0m"

    def __init__(
        self,
        fmt: str,
        datefmt: str | None = None,
        use_color: bool | None = None,
        level_width: int = 8,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        if use_color is None:
            use_color = sys.stderr.isatty() and "NO_COLOR" not in os.environ
        self.use_color = use_color
        self.level_width = level_width

    def format(self, record: logging.LogRecord) -> str:
        record_copy = logging.makeLogRecord(record.__dict__.copy())
        padded_level = f"{record_copy.levelname:<{self.level_width}}"
        if self.use_color:
            color = self.COLOR_MAP.get(record_copy.levelno)
            if color:
                padded_level = f"{color}{padded_level}{self.RESET}"
        record_copy.levelname = padded_level
        return super().format(record_copy)


def configure_logging() -> None:
    log_level = logging.DEBUG if LOG_LEVEL == "debug" else logging.INFO

    handlers: list[logging.Handler] = []

    # Try to set up file logging with proper directory creation
    try:
        # Ensure the logs directory exists
        LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Set up log file rotation handler; 5MB per log file, keeps 3 backups
        file_handler = RotatingFileHandler(LOGS_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)

        # JSON Formatter for file logs
        json_formatter = JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(json_formatter)
        handlers.append(file_handler)

    except (OSError, PermissionError) as e:
        # If file logging fails, continue with console logging only
        print(f"Warning: Could not set up file logging: {e}")
        print("Continuing with console logging only.")

    # Console Formatter for readability
    console_formatter = ColorFormatter(
        fmt="%(asctime)s - %(name)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # Configure the logger
    logging.basicConfig(level=log_level, handlers=handlers)

    # Silence noisy loggers after basicConfig
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("streamlit").setLevel(logging.INFO)

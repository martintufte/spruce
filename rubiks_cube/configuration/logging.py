import logging
import logging.config
from logging.handlers import RotatingFileHandler

from pythonjsonlogger import jsonlogger

from rubiks_cube.configuration import APP_MODE
from rubiks_cube.configuration.path_definitions import LOGS_PATH


def configure_logging() -> None:
    LOG_LEVEL = logging.DEBUG if APP_MODE == "development" else logging.INFO

    # Set up log file rotation handler; 5MB per log file, keeps 3 backups
    file_handler = RotatingFileHandler(LOGS_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)

    # JSON Formatter for file logs
    json_formatter = jsonlogger.JsonFormatter(  # type: ignore[no-untyped-call]
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(json_formatter)

    # Console Formatter for readability
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # Silence Matplotlib and PIL logs
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    # Configure the logger
    logging.basicConfig(level=LOG_LEVEL, handlers=[file_handler, console_handler])

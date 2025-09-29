import logging
import logging.config
from logging.handlers import RotatingFileHandler

from pythonjsonlogger.jsonlogger import JsonFormatter

from rubiks_cube.configuration import APP_MODE
from rubiks_cube.configuration.paths import LOGS_PATH


def configure_logging() -> None:
    log_level = logging.DEBUG if APP_MODE == "development" else logging.INFO

    handlers = []

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
        print(f"Continuing with console logging only.")

    # Console Formatter for readability
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
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

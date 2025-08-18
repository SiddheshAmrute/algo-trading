import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name="algo_trading", level=logging.INFO, log_dir="logs"):
    """
    Sets up a logger with console + file handlers.
    Uses rotating file logs to prevent unlimited growth.

    Args:
        name (str): Logger name (typically module/service name).
        level (int): Logging level.
        log_dir (str): Directory for log files.

    Returns:
        logging.Logger
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers in case of re-init
    if logger.hasHandlers():
        return logger

    # -------------------------------
    # Console Handler
    # -------------------------------
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "[%(asctime)s][%(name)s][%(levelname)s] → %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)

    # -------------------------------
    # File Handler with Rotation
    # -------------------------------
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f"{name}.log"),
        maxBytes=5 * 1024 * 1024,   # 5 MB per log file
        backupCount=5               # Keep 5 backups
    )
    file_formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] → %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Attach handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


from utils.logger import setup_logger
if __name__ == "__main__":

    logger = setup_logger("Logger")
    def test_logging():
        logger.debug("Debug message (for developers)")
        logger.info("Service started successfully 🚀")
        logger.warning("This is a warning — check config")
        logger.error("Something went wrong ❌")
        logger.critical("CRITICAL ERROR — Immediate attention needed")
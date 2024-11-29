import logging
from logging import Logger
from logging import StreamHandler, FileHandler, Formatter
import sys


def configure_logger() -> Logger:
    """
    Configure and return a logger with multiple handlers.

    Returns
    -------
    logging.Logger
        A configured logger with console and file handlers.

    Notes
    -----
    The logger is set up with two handlers:
    - A console handler logging at INFO level
    - A file handler logging at DEBUG level
    Both handlers use the same formatter for consistent log messages.
    """
    # Create logger
    logger: Logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Set logger to capture all levels

    # Create console handler
    console_handler: StreamHandler = StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Handler can filter messages

    # Create file handler for debug logs
    file_handler: FileHandler = FileHandler("debug.log")
    file_handler.setLevel(logging.DEBUG)  # Capture all debug messages

    # Create formatter
    formatter: Formatter = Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Prevent log propagation to parent loggers
    logger.propagate = False

    return logger

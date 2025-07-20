import logging
import sys
from typing import Optional


def create_scoped_logger(scope: str, level: Optional[str] = None) -> logging.Logger:
    """
    Create a scoped logger with consistent formatting

    Args:
        scope: The scope/name for the logger (e.g., "AbortRegistry", "ChatService")
        level: Optional log level ("DEBUG", "INFO", "WARNING", "ERROR").
               Defaults to "INFO" in production, "DEBUG" in development

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(scope)

    if logger.handlers:
        return logger

    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = logging.DEBUG

    logger.setLevel(log_level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    formatter = logging.Formatter(
        fmt='%(asctime)s - [ %(name)s ] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


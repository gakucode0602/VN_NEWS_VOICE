"""Logging configuration for RAG Service."""

import logging
import sys

# Log format matching ML Service
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Date format
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the entire application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing configuration
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Reduce noise from sentence-transformers
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info("Logging configured with level: %s", log_level.upper())


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

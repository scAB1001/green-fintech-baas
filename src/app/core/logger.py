# src/app/core/logger.py
import logging
import sys


def setup_logging() -> logging.Logger:
    """Configures industry-standard structured logging."""
    logger = logging.getLogger("green_fintech")

    # Only configure if no handlers exist to prevent duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = setup_logging()

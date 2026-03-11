# src/app/core/logger.py
"""
Application Logging Configuration.

This module provides a centralized, structured logging setup for the BaaS.
It ensures that all application logs are formatted consistently and streamed
to standard output (stdout), which is the industry standard for containerized
(Docker/Kubernetes) deployments.
"""

import logging
import sys


def setup_logging() -> logging.Logger:
    """
    Configures industry-standard structured logging for the application.

    Initializes a singleton-like logger instance. It explicitly checks for
    existing handlers to prevent log duplication, which commonly occurs during
    FastAPI/Uvicorn hot-reloads or when running the Pytest test suite.

    Returns:
        logging.Logger: The configured application logger instance.
    """
    logger = logging.getLogger("green_fintech")

    # Only attach a new handler if none exist to prevent duplicate log entries
    # across multiple module imports or Uvicorn worker restarts.
    if not logger.handlers:
        # INFO is the default level; debug statements are suppressed in production
        logger.setLevel(logging.INFO)

        # Standardize the log format for easy parsing by external monitoring tools
        # (e.g., DataDog, ELK stack)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Stream logs to stdout so Docker can capture the stream natively
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


# Instantiate a global logger instance to be imported across the application
logger = setup_logging()

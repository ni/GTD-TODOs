"""Structured logging configuration for the application."""

import logging
import sys


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Sets up the 'app' logger with a consistent format including
    timestamp, level, logger name, and message.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    # Avoid duplicate handlers on repeated calls (e.g. test reloads)
    if not app_logger.handlers:
        app_logger.addHandler(handler)

    # Also configure uvicorn access log format for consistency
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.handlers = [handler]

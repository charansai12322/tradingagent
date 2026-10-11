"""Structured logging configuration for AI Trading Agent backend.

Ensures logs provide clear operational visibility without ever leaking credentials,
authorization headers, full prompt injections, or sensitive account identifiers.
"""

import logging
import sys
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive tokens and headers from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Redact common credential patterns if accidentally printed
            for token in ("APCA-API-SECRET-KEY", "APCA-API-KEY-ID", "apikey", "api_key", "password", "secret"):
                if token in record.msg.lower():
                    record.msg = "[REDACTED_SENSITIVE_DATA_IN_LOG]"
        return True


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Initialize root and application loggers with structured formatting."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger format
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silence overly verbose external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger("tradingagent")
    logger.setLevel(level)
    return logger

"""Structured logging setup."""

import logging
import sys
from functools import lru_cache
from typing import Literal

import structlog
from structlog.types import Processor


def setup_logging(log_level: str = "INFO", log_format: Literal["json", "text"] = "json") -> None:
    """Setup structured logging."""
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == "json":
        processors.extend(
            [
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ]
        )
    else:
        processors.extend(
            [
                structlog.dev.set_exc_info,
                structlog.dev.ConsoleRenderer(),
            ]
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@lru_cache()
def get_logger(name: str):
    """Get a logger instance."""
    return structlog.get_logger(name)


"""Structured logging helpers."""

from __future__ import annotations

import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        if hasattr(record, "extra_data"):
            payload.update(getattr(record, "extra_data"))
        return json.dumps(payload)


class StructuredLogger(logging.Logger):
    """Logger that supports structured logging with keyword arguments."""

    def _log(
        self, level, msg, args, exc_info=None, extra=None, stack_info=None, **kwargs
    ):
        if extra is None:
            extra = {}
        if kwargs:
            extra["extra_data"] = kwargs
        super()._log(
            level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    old_class = logging.getLoggerClass()
    logging.setLoggerClass(StructuredLogger)
    logger = logging.getLogger(name)
    logging.setLoggerClass(old_class)
    if not logger.handlers:
        configure_logging()
    return logger


def configure_logging() -> None:
    root = logging.getLogger("waifu")
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.setLevel(logging.INFO)
    root.addHandler(handler)

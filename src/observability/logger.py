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


def configure_logging() -> None:
    root = logging.getLogger("waifu")
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.setLevel(logging.INFO)
    root.addHandler(handler)

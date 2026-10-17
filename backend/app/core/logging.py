"""Structured JSON logging configuration for DukaanFlow.

Emits Google Cloud Logging compatible JSON records on stdout with
automatic request_id correlation, latency, and secret masking.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class CloudJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON for Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()

        # Map python logging levels to Google Cloud severity levels
        severity_map = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }
        severity = severity_map.get(record.levelname, "INFO")

        payload: Dict[str, Any] = {
            "severity": severity,
            "timestamp": timestamp,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add correlation context if present
        if hasattr(record, "request_id"):
            payload["logging.googleapis.com/trace"] = getattr(record, "request_id")
            payload["request_id"] = getattr(record, "request_id")

        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            # Sanitize any sensitive fields
            sanitized = {
                k: ("***" if "password" in k.lower() or "token" in k.lower() or "secret" in k.lower() else v)
                for k, v in record.extra_fields.items()
            }
            payload.update(sanitized)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def setup_logging():
    """Initialize structured JSON logger on root logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CloudJsonFormatter())
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(CloudJsonFormatter())


logger = logging.getLogger("dukaanflow")

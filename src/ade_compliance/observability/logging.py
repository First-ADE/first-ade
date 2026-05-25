# implements: FR-026
# traces_to: Π.3.1

"""T073: Structured JSON logging for ADE Compliance Framework.

Provides a centralized, configurable structured logging setup
using Python's standard logging with JSON formatting.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines for structured log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields passed via logger.info("msg", extra={...})
        for key in ("action", "details", "axiom_id", "file_path", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


class ADELogger:
    """Wrapper around stdlib Logger that accepts extra kwargs for backward compatibility.

    This preserves the loguru-style API where callers can pass keyword arguments
    directly: ``logger.info("msg", action="foo", details={...})``
    and have them forwarded as ``extra=`` to the underlying stdlib logger.
    """

    _STANDARD_KWARGS = frozenset({"exc_info", "stack_info", "stacklevel", "extra"})

    def __init__(self, stdlib_logger: logging.Logger) -> None:
        self._logger = stdlib_logger

    # Expose common attributes so code like ``logger.handlers`` still works
    @property
    def handlers(self):
        return self._logger.handlers

    def setLevel(self, level: int) -> None:
        self._logger.setLevel(level)

    def addHandler(self, handler: logging.Handler) -> None:
        self._logger.addHandler(handler)

    # --- Logging methods with kwargs → extra forwarding ---

    def _log(self, level: int, msg: object, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        non_standard = {k: v for k, v in kwargs.items() if k not in self._STANDARD_KWARGS}
        for k in non_standard:
            kwargs.pop(k)
        extra.update(non_standard)
        self._logger.log(level, msg, *args, extra=extra, **kwargs)

    def debug(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: object, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("exc_info", True)
        self._log(logging.ERROR, msg, *args, **kwargs)


def setup_logging(
    level: int = logging.INFO,
    json_output: bool = True,
) -> ADELogger:
    """Configure the root ADE compliance logger.

    Args:
        level: Logging level (default: INFO).
        json_output: If True, use JSON formatting. If False, use human-readable.

    Returns:
        Configured ADELogger wrapping the ``ade_compliance`` stdlib logger.
    """
    root_logger = logging.getLogger("ade_compliance")

    # Avoid duplicate handlers
    if root_logger.handlers:
        return ADELogger(root_logger)

    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
            )
        )

    root_logger.addHandler(handler)
    return ADELogger(root_logger)


# Module-level logger instance for backward compatibility
logger = setup_logging(json_output=False)

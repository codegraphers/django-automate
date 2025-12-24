import json
import logging

from .context import get_trace_id


class JsonFormatter(logging.Formatter):
    """
    Structured JSON formatter that automatically injects trace_id and standardizes fields.
    """

    def format(self, record):
        trace_id = get_trace_id()

        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "trace_id": trace_id,
            "path": record.pathname,
            "line": record.lineno,
        }

        # Merge extra fields if present
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_record.update(record.extra_data)

        # Handle exceptions
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

import datetime
import json
import logging
from typing import Any

from automate_core.providers.base import ProviderContext


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "django-automate",
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Merge extra fields
        if hasattr(record, "ctx_fields") and isinstance(record.ctx_fields, dict):
            data.update(record.ctx_fields)

        if hasattr(record, "data") and isinstance(record.data, dict):
            # Redact data if needed (simple placeholder)
            data["data"] = record.data

        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(data)

class ContextAdapter(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger, ctx: ProviderContext | None = None):
        super().__init__(logger, {})
        self.ctx = ctx

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        extra = kwargs.get("extra", {})

        ctx_fields = {}
        if self.ctx:
            ctx_fields = {
                "tenant_id": self.ctx.tenant_id,
                "correlation_id": self.ctx.correlation_id,
                "actor_id": self.ctx.actor_id,
                "purpose": self.ctx.purpose
            }

        extra["ctx_fields"] = ctx_fields
        kwargs["extra"] = extra
        return msg, kwargs

def get_logger(name: str, ctx: ProviderContext | None = None) -> logging.LoggerAdapter:
    logger = logging.getLogger(name)
    return ContextAdapter(logger, ctx)

def configure_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

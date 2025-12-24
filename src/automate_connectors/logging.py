from __future__ import annotations
import logging
import time
import functools
from typing import Any, Callable

logger = logging.getLogger(__name__)

def trace_connector_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for ConnectorAdapter.execute to emit structured logs.
    """
    @functools.wraps(func)
    def wrapper(self, action: str, input: Any, ctx: Any, *args, **kwargs):
        start_ts = time.time()
        connector_code = getattr(self, "code", "unknown")
        trace_id = ctx.get("trace_id", "unknown")
        
        try:
            result = func(self, action, input, ctx, *args, **kwargs)
            duration_ms = (time.time() - start_ts) * 1000
            
            logger.info(
                "Connector Execution Success",
                extra={
                    "connector": connector_code,
                    "action": action,
                    "trace_id": trace_id,
                    "duration_ms": duration_ms,
                    "status": "success",
                }
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_ts) * 1000
            error_code = getattr(e, "code", "INTERNAL_ERROR")
            
            logger.error(
                "Connector Execution Failed",
                extra={
                    "connector": connector_code,
                    "action": action,
                    "trace_id": trace_id,
                    "duration_ms": duration_ms,
                    "status": "failed",
                    "error_code": str(error_code),
                    "error_message": str(e)
                }
            )
            raise
            
    return wrapper

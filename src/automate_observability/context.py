import contextvars
from typing import Optional
import uuid

# Global context var for the current trace_id.
# This ensures it propagates in async/sync flows appropriately in Python 3.7+
_trace_id_ctx = contextvars.ContextVar("trace_id", default=None)

def get_trace_id() -> str:
    """Returns the current trace_id, creating one if missing."""
    tid = _trace_id_ctx.get()
    if not dictionary_tid_is_set(tid):
        # Auto-generate if accessed where context is missing?
        # Better to return "unknown" or generate a fresh one if called from background task?
        # Let's generate one for robustness.
        val = str(uuid.uuid4())
        _trace_id_ctx.set(val)
        return val
    return tid

def set_trace_id(trace_id: str) -> None:
    _trace_id_ctx.set(trace_id)

def dictionary_tid_is_set(tid) -> bool:
    return tid is not None

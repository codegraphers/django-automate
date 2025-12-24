from typing import Any

from .context import get_trace_id
from .models import AuditLogEntry


def log_audit_event(
    *,
    actor: str,
    action: str,
    obj_type: str = "",
    obj_id: str = "",
    details: dict[str, Any] = None,
) -> AuditLogEntry:
    """
    Write an audit log entry.
    Ensure 'details' is already redacted/safe before calling this.
    """
    return AuditLogEntry.objects.create(
        actor=actor,
        action=action,
        object_type=obj_type,
        object_id=obj_id,
        trace_id=get_trace_id() or "unknown",
        details=details or {}
    )

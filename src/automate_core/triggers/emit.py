from __future__ import annotations

import hashlib
import json
from typing import Any

from django.utils import timezone

# We need the Event model. It's in the Plan as src/automate_core/events/models.py
# I haven't implemented it yet, but I can reference it or assume it exists.
# For now, I will create the function logic and import the model once it's created.
# Wait, I should implement events/models.py first according to dependency order.
# But following the "Trigger System" task, "emit.py" is listed.
# I will implement the Emission logic assuming the Event model structure.

def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Canonical SHA256 hash of payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def emit_event(
    *,
    tenant_id: str,
    event_type: str,
    source: str,
    payload: dict[str, Any],
    trigger_id: int | None = None,
    idempotency_key: str | None = None
) -> Any:
    """
    Emit a canonical event to the DB (and subsequently Outbox).
    """
    # Circular dependency avoidance: Import inside function or ensure order.
    from automate_core.events.models import Event

    payload_hash = compute_payload_hash(payload)

    # Dedupe check (if idempotency_key provided)
    if idempotency_key and Event.objects.filter(tenant_id=tenant_id, idempotency_key=idempotency_key).exists():
        return None # Already exists

    event = Event.objects.create(
        tenant_id=tenant_id,
        event_type=event_type,
        source=source,
        trigger_id=trigger_id,
        payload=payload,
        payload_hash=payload_hash,
        idempotency_key=idempotency_key,
        occurred_at=timezone.now()
    )

    # TODO: Enqueue to Outbox (kind="event_dispatch")
    # from automate_core.outbox.store import get_store
    # get_store().enqueue(...)

    return event

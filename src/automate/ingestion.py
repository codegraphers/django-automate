import logging

from django.db import transaction

from .models import Event, Outbox

logger = logging.getLogger(__name__)

class EventIngestionService:
    @staticmethod
    def ingest_event(
        event_type: str,
        source: str,
        payload: dict,
        actor_id: str = None,
        idempotency_key: str = None,
        tenant_id: str = "default",
    ) -> Event:
        """
        Ingests an event transactionally, creating both the Event record
        and the Outbox entry to ensure it gets processed.
        P0.3: Robust idempotency using DB constraints.
        """
        from django.utils import timezone
        
        if idempotency_key:
            # First check efficiently
            existing = Event.objects.filter(tenant_id=tenant_id, idempotency_key=idempotency_key).first()
            if existing:
                logger.info(f"Duplicate event deduplicated (pre-check): {idempotency_key}")
                return existing

        try:
            with transaction.atomic():
                context = {}
                if actor_id:
                    context["actor_id"] = actor_id
                    
                event = Event.objects.create(
                    tenant_id=tenant_id,
                    event_type=event_type,
                    source=source,
                    payload=payload,
                    context=context,
                    idempotency_key=idempotency_key,
                    occurred_at=timezone.now()
                )

                # Canonical OutboxItem (Generic)
                # We replicate "event" linkage via payload
                Outbox.objects.create(
                    tenant_id=tenant_id,
                    kind="event",
                    payload={"event_id": str(event.id)},
                    status="PENDING", # Default
                    priority=100
                )

                logger.info(f"Event ingested: {event.id} ({event_type})")
                return event
        except Exception as e:
            # Handle potential race condition where another process created it since the pre-check
            if idempotency_key:
                existing = Event.objects.filter(tenant_id=tenant_id, idempotency_key=idempotency_key).first()
                if existing:
                    logger.info(f"Duplicate event deduplicated (race-catch): {idempotency_key}")
                    return existing

            # If it wasn't an integrity error on idempotency_key, or key wasn't set, re-raise
            raise e

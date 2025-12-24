import hashlib
import json
import logging
import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone

from ...executions.models import Execution, ExecutionStatusChoices
from ...outbox.models import OutboxItem
from ...workflows.models import Trigger
from ..models import Event

logger = logging.getLogger(__name__)


class EventIngestor:
    """
    Atomic service to ingest events and trigger automations reliably.
    Guarantees:
    - Idempotency (if key provided)
    - Zero data loss (transactional Outbox pattern)
    - strict matching logic
    """

    def ingest(
        self,
        tenant_id: str,
        event_type: str,
        source: str,
        payload: dict,
        idempotency_key: str = None,
        context: dict = None,
    ) -> Event:
        # 1. Normalize
        correlation_id = context.get("correlation_id") if context else str(uuid.uuid4())
        if not context:
            context = {}
        context["correlation_id"] = correlation_id

        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        # 2. Idempotency Check (Pre-DB)
        # We rely on DB constraint, but can check optimization here if needed.

        try:
            with transaction.atomic():
                # 3. Create Event (Source of Truth)
                event = Event.objects.create(
                    tenant_id=tenant_id,
                    event_type=event_type,
                    source=source,
                    payload=payload,
                    payload_hash=payload_hash,
                    idempotency_key=idempotency_key,
                    context=context,
                    occurred_at=timezone.now(),
                    status="dispatched",
                )

                # 4. Strictly Match Triggers
                # Find all ACTIVE triggers matching this type
                # TODO: Implement complex filtering (Rule Engine match)
                triggers = Trigger.objects.filter(
                    automation__tenant_id=tenant_id,
                    automation__is_active=True,
                    is_active=True,
                    event_type=event_type,  # Exact match or implement pattern match logic
                ).select_related("automation")

                dispatch_count = 0

                for trigger in triggers:
                    # 4b. Apply detailed filter config (JSONLogic)
                    if not self._matches_filter(trigger, payload):
                        continue

                    # 5. Create Execution
                    execution = Execution.objects.create(
                        tenant_id=tenant_id,
                        event=event,
                        automation=trigger.automation,
                        trigger=trigger,
                        workflow_version=1,  # TODO: Get HEAD version
                        status=ExecutionStatusChoices.QUEUED,
                        correlation_id=correlation_id,
                        context=context,
                    )

                    # 6. Create Outbox Item (The Reliability Promise)
                    OutboxItem.objects.create(
                        tenant_id=tenant_id,
                        kind="execution_queued",
                        payload={"execution_id": str(execution.id)},
                        status="PENDING",
                        priority=trigger.priority,
                    )
                    dispatch_count += 1

                logger.info(f"Ingested event {event.id}: Dispatched {dispatch_count} executions.")
                return event

        except IntegrityError as e:
            if "unique_event_idempotency" in str(e) or "event_idempotency_uniq" in str(e):
                logger.warning(f"Idempotent duplicate ignored: {idempotency_key}")
                return Event.objects.get(tenant_id=tenant_id, idempotency_key=idempotency_key)
            raise e

    def _matches_filter(self, trigger: Trigger, payload: dict) -> bool:
        """
        Evaluate JSONLogic or simple filters.
        """
        if not trigger.filter_config:
            return True

        # TODO: Implement robust JSONLogic evaluation
        # For now, minimal key-value match
        return all(payload.get(k) == v for k, v in trigger.filter_config.items())

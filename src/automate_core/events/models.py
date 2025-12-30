import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from automate_core.base.models import ValidatableMixin


class EventStatusChoices(models.TextChoices):
    NEW = "new", _("New")
    DISPATCHED = "dispatched", _("Dispatched")
    PROCESSING = "processing", _("Processing")
    DONE = "done", _("Done")
    FAILED = "failed", _("Failed")


class Event(ValidatableMixin, models.Model):
    """
    Immutable canonical event log.
    Single source of truth for all ingress facts.

    Inherits:
        ValidatableMixin: Provides validate_fields() hook

    Override Points:
        - validate_payload(): Validate event payload
        - compute_payload_hash(): Customize hash computation
        - get_context(): Get event context

    Configuration:
        Override class attributes to customize behavior.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)

    # Classification
    event_type = models.CharField(max_length=128, db_index=True)  # e.g. "order.created"
    source = models.CharField(max_length=64)  # "webhook", "signal", "schedule", "admin"

    # Traceability
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    trigger_id = models.IntegerField(null=True, blank=True)  # pointer to TriggerSpec (Legacy/Optional?)

    # Timing
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Data
    payload = models.JSONField(default=dict)
    payload_hash = models.CharField(max_length=64)  # SHA256 of canonical payload

    # Idempotency
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)

    # Context (Actor, Request Metadata)
    context = models.JSONField(default=dict)

    # Lifecycle
    status = models.CharField(
        max_length=20, choices=EventStatusChoices.choices, default=EventStatusChoices.NEW, db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["tenant_id", "occurred_at"]),
            models.Index(fields=["tenant_id", "event_type", "occurred_at"]),
            models.Index(fields=["status", "created_at"]),  # For worker polling
        ]
        # Unique constraint for idempotency
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "source", "idempotency_key"],
                name="event_idempotency_uniq",
                condition=models.Q(idempotency_key__isnull=False),
            )
        ]

    def __str__(self):
        return f"{self.event_type} ({self.id})"

    def validate_payload(self) -> dict:
        """Validate event payload. Override to customize."""
        return {}

    def validate_fields(self):
        errors = super().validate_fields()
        errors.update(self.validate_payload())
        return errors

    def compute_payload_hash(self) -> str:
        """Compute hash of payload. Override to customize."""
        import hashlib
        import json
        serialized = json.dumps(self.payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def get_context(self) -> dict:
        """Get event context with defaults. Override to customize."""
        return {
            'correlation_id': str(self.correlation_id),
            'tenant_id': self.tenant_id,
            'event_type': self.event_type,
            **self.context,
        }

    def mark_processed(self):
        """Mark event as processed."""
        self.status = EventStatusChoices.DONE
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])


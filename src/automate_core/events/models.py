from django.db import models
from django.utils import timezone

class Event(models.Model):
    """
    Immutable canonical event log.
    """
    tenant_id = models.CharField(max_length=64, db_index=True)
    event_type = models.CharField(max_length=128, db_index=True)  # e.g. "order.created"
    
    source = models.CharField(max_length=64) # "webhook", "signal", "schedule", "admin"
    trigger_id = models.IntegerField(null=True, blank=True) # pointer to TriggerSpec
    
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(default=timezone.now)
    
    payload = models.JSONField(default=dict)
    payload_hash = models.CharField(max_length=64) # SHA256 of canonical payload
    
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    
    context = models.JSONField(default=dict) # correlation_id, request_id, actor
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "occurred_at"]),
            models.Index(fields=["tenant_id", "event_type", "occurred_at"]),
        ]
        # Unique constraint for idempotency
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "idempotency_key"],
                name="event_idempotency_uniq",
                condition=models.Q(idempotency_key__isnull=False),
            )
        ]

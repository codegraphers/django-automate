from django.db import models
from django.utils import timezone

class OutboxItem(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("RETRY", "Retry"),
        ("DLQ", "Dead Letter Queue"),
        ("DONE", "Done"),
        ("CANCELLED", "Cancelled"),
    ]

    tenant_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="PENDING")
    kind = models.CharField(max_length=64)  # "event", "step", "webhook"
    
    payload = models.JSONField(default=dict)

    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    priority = models.IntegerField(default=100)

    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=15)
    next_attempt_at = models.DateTimeField(default=timezone.now)

    lease_owner = models.CharField(max_length=128, null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)

    last_error_code = models.CharField(max_length=128, null=True, blank=True)
    last_error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "next_attempt_at"]),
            models.Index(fields=["tenant_id", "status", "next_attempt_at"]),
        ]
        # Partial unique index for idempotency is DB-specific (Postgres)
        # We will enforce this via application logic or standard unique constraints where possible.
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "idempotency_key"],
                name="outbox_idempotency_uniq",
                condition=models.Q(idempotency_key__isnull=False),
            )
        ]

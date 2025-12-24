import uuid

from django.db import models


class AuditLogEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    actor = models.CharField(max_length=255, help_text="User or Service Account", db_index=True)
    action = models.CharField(max_length=100, db_index=True)  # e.g. WORKFLOW_PUBLISHED

    # Polymorphic-ish reference
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=255, blank=True)

    trace_id = models.CharField(max_length=64, blank=True, db_index=True)

    details = models.JSONField(default=dict, help_text="Redacted details")

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["actor", "action"]),
        ]

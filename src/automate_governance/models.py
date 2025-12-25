import uuid

from django.db import models


class AuditLog(models.Model):
    """
    Immutable security log of all significant actions.
    Append-only.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=50, db_index=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Actor (Who)
    actor = models.JSONField(default=dict, help_text="{'type': 'user|token|system', 'id': '...', 'name': '...'}")

    # Action (What)
    action = models.CharField(max_length=100, db_index=True, help_text="e.g. endpoint.run")
    resource = models.JSONField(default=dict, help_text="{'type': '...', 'id': '...'}")

    # Context (Where/How)
    result = models.CharField(max_length=20, choices=[
        ("allowed", "Allowed"), ("denied", "Denied"),
        ("success", "Success"), ("failure", "Failure")
    ])
    correlation_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Payload (What Data) - MUST BE REDACTED
    payload_redacted = models.JSONField(default=dict)

    # Tamper Evidence (Foundation)
    # hash = sha256(prev_hash + self.data) - simplified here as placeholder
    hash = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["action", "occurred_at"]),
            models.Index(fields=["actor"]),
        ]

    def __str__(self):
        return f"{self.occurred_at} | {self.action} | {self.result} | {self.actor.get('id')}"

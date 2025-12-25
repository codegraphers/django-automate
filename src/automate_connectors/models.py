import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class ConnectorStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    DISABLED = "disabled", _("Disabled")
    ERROR = "error", _("Error")

class ConnectorInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    connector_key = models.CharField(max_length=64, db_index=True) # e.g. "slack", "github"
    name = models.CharField(max_length=255)

    # Configuration containing SecretRefs
    config = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        choices=ConnectorStatus.choices,
        default=ConnectorStatus.ACTIVE
    )

    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One type of connector per tenant can have multiple instances (e.g. 2 Slack workspaces)
        # So no unique together on (tenant, connector_key)
        indexes = [
            models.Index(fields=["tenant_id", "connector_key"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.connector_key})"

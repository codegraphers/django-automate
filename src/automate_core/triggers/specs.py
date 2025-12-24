from django.db import models

class TriggerSpec(models.Model):
    """
    Defines a trigger that ingests events.
    """
    TRIGGER_TYPES = [
        ("WEBHOOK", "Webhook"),
        ("SCHEDULE", "Schedule"),
        ("SIGNAL", "Signal"),
        ("ADMIN_ACTION", "Admin Action"),
    ]

    tenant_id = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=128)
    kind = models.CharField(max_length=32, choices=TRIGGER_TYPES)
    
    # Typed config depending on kind
    # Webhook: { "path": "/foo", "method": "POST", "signature_secret": "..." }
    # Schedule: { "cron": "0 * * * *", "timezone": "UTC" }
    config = models.JSONField(default=dict)
    
    enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [("tenant_id", "name")]

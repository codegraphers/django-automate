from django.db import models


class ConnectionProfile(models.Model):
    kind = models.CharField(max_length=64)  # "stripe", "openai", "slack"
    name = models.CharField(max_length=128)

    config = models.JSONField(default=dict)  # non-secret config only
    secrets = models.JSONField(default=dict)  # { "api_key": "secretref://..." }

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional tenant logic (to be integrated properly later)
    tenant_id = models.CharField(max_length=64, db_index=True)

    class Meta:
        unique_together = [("tenant_id", "kind", "name")]


class StoredSecret(models.Model):
    namespace = models.CharField(max_length=128, db_index=True)
    name = models.CharField(max_length=128, db_index=True)

    # ciphertext stored as bytes/base64; db-agnostic
    ciphertext = models.BinaryField()

    version = models.IntegerField(default=1)
    is_current = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("namespace", "name", "version")]
        indexes = [
            models.Index(fields=["namespace", "name", "is_current"]),
        ]

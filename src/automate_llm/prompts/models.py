from django.db import models


class PromptTemplate(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=128)
    version = models.IntegerField(default=1)

    # Jinja2 template content
    template_text = models.TextField()

    # JSON Schema for expected input variables (for validation/UI)
    input_schema = models.JSONField(default=dict)

    # Provider-specific config defaults (e.g. default temperature)
    config = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant_id", "name", "version")]
        indexes = [
            models.Index(fields=["tenant_id", "name", "is_active"]),
        ]

import uuid

from django.db import models

# Re-export strict imports for backward compat within the module if needed,
# although PromptTemplate is gone, we might add a shim if necessary.
# But for this refactor, we replace it.

class LLMUsage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    correlation_id = models.CharField(max_length=64, db_index=True)

    # Context
    job_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    step_run_id = models.CharField(max_length=64, blank=True, null=True)

    # Provider Info
    provider_key = models.CharField(max_length=64)
    model = models.CharField(max_length=128)

    # Token Accounting
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    cache_hit_tokens = models.IntegerField(default=0)

    # Cost
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    pricing_version = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "created_at"]),
        ]

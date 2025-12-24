from django.db import models


class LLMRequest(models.Model):
    """
    Audit log for every LLM interaction.
    Critical for cost tracking and governance.
    """
    tenant_id = models.CharField(max_length=64, db_index=True, default="default")
    provider = models.CharField(max_length=64) # "openai", "anthropic"
    model = models.CharField(max_length=128)   # "gpt-4-turbo"

    # Context for traceability
    prompt_slug = models.CharField(max_length=128, blank=True)  # e.g., "datachat_sql_generator"
    purpose = models.CharField(max_length=64, blank=True)  # e.g., "sql_generation", "summarization"

    input_tokens = models.IntegerField(null=True)
    output_tokens = models.IntegerField(null=True)

    cost_usd = models.DecimalField(max_digits=12, decimal_places=6, null=True)
    latency_ms = models.IntegerField(null=True)

    status = models.CharField(max_length=32) # SUCCESS, FAILED, BLOCKED
    error_message = models.TextField(blank=True)

    # Store full request/response for debugging and eval
    input_payload = models.JSONField(null=True, blank=True, help_text="Messages sent to LLM")
    output_content = models.TextField(blank=True, help_text="Raw LLM response text")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "created_at"]),
            models.Index(fields=["purpose", "created_at"]),
        ]

    def __str__(self):
        return f"{self.provider}/{self.model} - {self.purpose} ({self.status})"



from django.db import models
from django.contrib.postgres.indexes import GinIndex

class RuleSpec(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=128)
    
    rule_json = models.JSONField(default=dict)
    
    # Extracted terms for optimization
    # ["event.type=order.created", "event.source=shopify"]
    index_terms = models.JSONField(default=list)
    
    enabled = models.BooleanField(default=True)
    priority = models.IntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant_id", "name")]
        indexes = [
            # Standard index
            models.Index(fields=["tenant_id", "enabled", "priority"]),
            
            # GIN Index for fast term matching (Postgres only)
            # Check availability or use conditional migration in real app
            # GinIndex(fields=["index_terms"], name="rule_terms_gin"),
        ]

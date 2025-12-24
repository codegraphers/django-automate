import uuid
from django.db import models

class PolicyScopeChoices(models.TextChoices):
    GLOBAL = "global", "Global"
    AUTOMATION = "automation", "Automation" 
    ENDPOINT = "endpoint", "Endpoint" # e.g. a specific LLM endpoint
    USER = "user", "User"

class Policy(models.Model):
    """
    Governance rules: RBAC, Budget, Rate Limits, Redaction.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    
    scope = models.CharField(max_length=32, choices=PolicyScopeChoices.choices, default=PolicyScopeChoices.GLOBAL)
    target_id = models.UUIDField(null=True, blank=True, db_index=True) # ID of Automation or User
    
    name = models.CharField(max_length=255)
    
    # The actual policy definition
    # {
    #   "budget": { "daily_usd": 10.0 },
    #   "redaction": ["credit_card", "ssn"],
    #   "access": { "roles": ["admin"] }
    # }
    rules = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "scope", "target_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.scope})"

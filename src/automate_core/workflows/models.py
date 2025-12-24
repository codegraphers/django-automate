import uuid
import hashlib
import json
from django.db import models

class Automation(models.Model):
    """
    Root entity for a defined automation process.
    Multi-tenant, versioned container.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    slug = models.SlugField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant_id", "slug")]
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self):
        return f"{self.slug} (v{self.workflows.count()})"

class Workflow(models.Model):
    """
    Immutable version of an automation logic (DAG).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(Automation, related_name="workflows", on_delete=models.CASCADE)
    version = models.IntegerField(default=1)
    
    # Graphs
    graph = models.JSONField(default=dict)
    
    # Immutability
    hash = models.CharField(max_length=64, editable=False)
    
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("automation", "version")
        ordering = ["-version"]
        
    def save(self, *args, **kwargs):
        if not self.hash:
            # Calculate deterministic hash of graph
            serialized = json.dumps(self.graph, sort_keys=True).encode("utf-8")
            self.hash = hashlib.sha256(serialized).hexdigest()
        super().save(*args, **kwargs)

class Trigger(models.Model):
    """
    Configuration for what triggers an automation.
    Links an automation to event matching logic.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(Automation, related_name="triggers", on_delete=models.CASCADE)
    
    type = models.CharField(max_length=50, choices=[
        ("model_signal", "Model Signal"),
        ("webhook", "Webhook"),
        ("schedule", "Schedule"),
        ("manual", "Manual"),
        ("external", "External"),
    ], db_index=True)
    
    event_type = models.CharField(max_length=255, help_text="Event type pattern to match (e.g. order.*)")
    
    # Matching Logic
    filter_config = models.JSONField(default=dict, help_text="JSONLogic/filtering rules")
    
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["type", "event_type"]),
        ]

    def __str__(self):
        return f"{self.type}/{self.event_type} -> {self.automation.slug}"

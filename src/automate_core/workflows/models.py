import uuid
from django.db import models

class Automation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant_id", "slug")]

class Workflow(models.Model):
    automation = models.ForeignKey(Automation, related_name="workflows", on_delete=models.CASCADE)
    version = models.IntegerField(default=1)
    graph = models.JSONField(default=dict)
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("automation", "version")
        ordering = ["-version"]

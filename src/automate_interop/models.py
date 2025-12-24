from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class InteropMapping(models.Model):
    """
    Maps a local django_automate workflow to an external orchestrator workflow.
    Tracks drift/sync state.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local_workflow_id = models.CharField(max_length=255, help_text="ID/Slug of local workflow")
    orchestrator_instance = models.CharField(max_length=255, default="n8n:primary")
    remote_workflow_id = models.CharField(max_length=255, help_text="ID of external workflow")
    
    last_synced_at = models.DateTimeField(null=True, blank=True)
    local_hash = models.CharField(max_length=64, blank=True)
    remote_hash = models.CharField(max_length=64, blank=True)
    
    drift_state = models.CharField(max_length=50, default="UNKNOWN")

    class Meta:
        indexes = [
            models.Index(fields=["local_workflow_id"]),
            models.Index(fields=["remote_workflow_id"]),
        ]

class TemplateCollection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    rank = models.IntegerField(default=0)

class TemplateWorkflow(models.Model):
    """
    A stored template served via the Template Host API.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    workflow_json = models.JSONField(default=dict)
    
    collection = models.ForeignKey(TemplateCollection, on_delete=models.SET_NULL, null=True, related_name="workflows")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

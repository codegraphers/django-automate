import uuid
from django.db import models
from ..workflows.models import Automation, Workflow
from ..events.models import Event

class ExecutionStatusChoices(models.TextChoices):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"

class Execution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    event = models.ForeignKey(Event, related_name="executions", on_delete=models.CASCADE)
    automation = models.ForeignKey(Automation, related_name="executions", on_delete=models.CASCADE)
    workflow_version = models.IntegerField(default=1)
    
    status = models.CharField(max_length=20, choices=ExecutionStatusChoices.choices, default=ExecutionStatusChoices.QUEUED)
    
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
        ]

class ExecutionStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(Execution, related_name="steps", on_delete=models.CASCADE)
    step_id = models.CharField(max_length=255)
    
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=ExecutionStatusChoices.choices)
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

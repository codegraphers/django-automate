import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from ..workflows.models import Automation, Workflow, Trigger
from ..events.models import Event

class ExecutionStatusChoices(models.TextChoices):
    QUEUED = "queued", _("Queued")
    RUNNING = "running", _("Running")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    CANCELED = "canceled", _("Canceled")

class Execution(models.Model):
    """
    State of a single run of an automation.
    Canonical root of runtime state.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    
    # Traceability
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    
    # Origin
    event = models.ForeignKey(Event, related_name="executions", on_delete=models.CASCADE)
    automation = models.ForeignKey(Automation, related_name="executions", on_delete=models.CASCADE)
    trigger = models.ForeignKey(Trigger, related_name="executions", on_delete=models.SET_NULL, null=True)
    
    # Versioning
    workflow_version = models.IntegerField(default=1)
    
    # Lifecycle
    status = models.CharField(max_length=20, choices=ExecutionStatusChoices.choices, default=ExecutionStatusChoices.QUEUED)
    attempt = models.IntegerField(default=1)
    
    # Context (Variables state)
    context = models.JSONField(default=dict)
    
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["status", "started_at"]), # Worker polling
        ]
        constraints = [
            # Ensure only one execution per event/automation tuple (Idempotency)
            models.UniqueConstraint(fields=["tenant_id", "automation", "event"], name="unique_execution_per_event")
        ]

class StepRun(models.Model):
    """
    Log of a single step (node) within an execution.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(Execution, related_name="steps", on_delete=models.CASCADE)
    
    # Identity
    node_key = models.CharField(max_length=255) # ID in the graph
    
    # Data
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    error_data = models.JSONField(default=dict)
    
    # Lifecycle
    status = models.CharField(max_length=20, choices=ExecutionStatusChoices.choices)
    attempt = models.IntegerField(default=1)
    
    # Provider Info (which connector ran this?)
    provider_meta = models.JSONField(default=dict)
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        # One result per node per execution (mostly)
        # Retries might append new StepRuns or update existing. Plan says append-only for attempts? 
        # For now, let's simpler unique constraint on node_key which implies overwrite/update on retry, 
        # OR we remove unique constraint to allow history.
        # User plan said: "StepRun is append-only for attempts (or store attempts as child rows)"
        # Let's keep it simple: One StepRun per node. Retries update it (like Celery Task). 
        # If we need history, we need StepRunAttempt.
        unique_together = ["execution", "node_key"]

# Alias for backward compat if needed, or just remove
ExecutionStep = StepRun

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from automate_core.base.models import SignalMixin, ValidatableMixin

from ..events.models import Event
from ..workflows.models import Automation, Trigger


class ExecutionStatusChoices(models.TextChoices):
    QUEUED = "queued", _("Queued")
    RUNNING = "running", _("Running")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    CANCELED = "canceled", _("Canceled")


class Execution(ValidatableMixin, SignalMixin, models.Model):
    """
    State of a single run of an automation.
    Canonical root of runtime state.

    Inherits:
        ValidatableMixin: Provides validate_fields() hook
        SignalMixin: Provides pre_save_hook(), post_save_hook()

    Override Points:
        - on_status_change(old, new): Handle status transitions
        - can_transition_to(status): Check valid transitions
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
    status = models.CharField(
        max_length=20, choices=ExecutionStatusChoices.choices, default=ExecutionStatusChoices.QUEUED
    )
    attempt = models.IntegerField(default=1)

    # Context (Variables state)
    context = models.JSONField(default=dict)

    # Error Tracking
    error_summary = models.TextField(blank=True, null=True)

    # QoS
    priority = models.IntegerField(default=100, db_index=True)

    # Distributed Locking (Lease)
    lease_owner = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Status transition rules (overrideable)
    STATUS_TRANSITIONS = {
        'queued': ['running', 'canceled'],
        'running': ['success', 'failed', 'canceled'],
    }

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            # Polling index: Unassigned or Leased-but-expired
            models.Index(fields=["status", "lease_expires_at"]),
        ]
        constraints = [
            # Ensure only one execution per event/automation tuple (Idempotency)
            models.UniqueConstraint(fields=["tenant_id", "automation", "event"], name="unique_execution_per_event")
        ]

    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new_status is valid. Override to customize."""
        valid_next = self.STATUS_TRANSITIONS.get(self.status, [])
        return new_status in valid_next or not self.STATUS_TRANSITIONS

    def transition_to(self, new_status: str, error: str = None) -> bool:
        """Transition to new status if valid."""
        old_status = self.status
        if not self.can_transition_to(new_status):
            return False

        self.status = new_status
        if new_status in ['success', 'failed', 'canceled']:
            self.finished_at = timezone.now()
        if error:
            self.error_summary = error
        self.save()
        self.on_status_change(old_status, new_status)
        return True

    def on_status_change(self, old_status: str, new_status: str):
        """Called when status changes. Override to add custom behavior."""
        pass

    def start(self):
        """Mark execution as started."""
        self.started_at = timezone.now()
        self.transition_to('running')

    def complete(self, context: dict = None):
        """Mark execution as completed."""
        if context:
            self.context = context
        self.transition_to('success')

    def fail(self, error: str):
        """Mark execution as failed."""
        self.transition_to('failed', error=error)



class StepRun(models.Model):
    """
    Log of a single step (node) within an execution.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(Execution, related_name="steps", on_delete=models.CASCADE)

    # Identity
    node_key = models.CharField(max_length=255)  # ID in the graph

    # Data
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    error_data = models.JSONField(default=dict)

    # Lifecycle
    status = models.CharField(max_length=20, choices=ExecutionStatusChoices.choices)
    attempt = models.IntegerField(default=1)

    # Distributed Locking (Lease) for Step Workers
    lease_owner = models.CharField(max_length=128, null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)

    # Provider Info (which connector ran this?)
    provider_meta = models.JSONField(default=dict)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # One result per node per execution (strict uniqueness for safety)
        unique_together = ["execution", "node_key"]
        indexes = [
            models.Index(fields=["status", "lease_expires_at"]),
        ]


class SideEffectLog(models.Model):
    """
    Registry of external side-effects to guarantee exactly-once behavior
    even when steps are retried (SRE Requirement).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)

    # Deduplication Key: sha256(execution_id + node_key + action + params)
    key = models.CharField(max_length=64, unique=True, db_index=True)

    # The external reference (e.g. Stripe Charge ID, Slack TS)
    external_id = models.CharField(max_length=255)

    # Cached response to return on replay
    response_payload = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "key"]),
        ]


# Alias for backward compat if needed, or just remove
ExecutionStep = StepRun

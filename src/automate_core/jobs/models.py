import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from automate_core.base.models import SignalMixin, ValidatableMixin


class JobStatusChoices(models.TextChoices):
    CREATED = "created", _("Created")
    QUEUED = "queued", _("Queued")
    RUNNING = "running", _("Running")
    RETRY_SCHEDULED = "retry_scheduled", _("Retry Scheduled")
    SUCCEEDED = "succeeded", _("Succeeded")
    FAILED = "failed", _("Failed")
    DLQ = "dlq", _("Dead Letter Queue")
    CANCELED = "canceled", _("Canceled")


class JobKindChoices(models.TextChoices):
    EXECUTION = "execution", _("Execution")
    STEP = "step", _("Step")
    MODAL = "modal", _("Modal Call")
    RAG = "rag", _("RAG Operation")
    CONNECTOR = "connector", _("Connector Sync")
    CUSTOM = "custom", _("Custom")


class BackendTypeChoices(models.TextChoices):
    CELERY = "celery", _("Celery")
    OUTBOX_DB = "outbox-db", _("DB Outbox")
    RQ = "rq", _("Redis Queue")
    SQS = "sqs", _("SQS Direct")


class Job(ValidatableMixin, SignalMixin, models.Model):
    """
    The canonical unit of work.
    Parity model: State is owned here, Backend is just a transport.

    Inherits:
        ValidatableMixin: Provides validate_fields() hook
        SignalMixin: Provides pre_save_hook(), post_save_hook()

    Override Points:
        - on_status_change(old, new): Handle status transitions
        - can_transition_to(status): Check valid transitions
        - execute(): Execute job logic
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=50, blank=True, db_index=True)

    # Classification
    kind = models.CharField(max_length=50, choices=JobKindChoices.choices, default=JobKindChoices.CUSTOM)
    topic = models.CharField(max_length=255, help_text="e.g. execution.run, step.run")

    # Data
    payload_redacted = models.JSONField(default=dict, help_text="Redacted payload for execution")

    # State & Scheduling
    status = models.CharField(
        max_length=50,
        choices=JobStatusChoices.choices,
        default=JobStatusChoices.CREATED,
        db_index=True
    )

    queue_name = models.CharField(max_length=100, default="default")
    priority = models.IntegerField(default=10, help_text="Lower is higher priority (1-100)")

    # Attempts
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_attempt_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Backend Transport Info
    backend = models.CharField(max_length=50, choices=BackendTypeChoices.choices, default=BackendTypeChoices.CELERY)
    backend_task_id = models.CharField(max_length=255, null=True, blank=True, help_text="e.g. Celery Task ID")
    backend_message_id = models.CharField(max_length=255, null=True, blank=True, help_text="SQS/Rabbit Message ID")

    # Concurrency Control (Lease)
    lease_owner = models.CharField(max_length=255, null=True, blank=True, help_text="Worker ID owning this job")
    lease_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)

    # Results
    result_summary = models.JSONField(default=dict, blank=True)
    error_redacted = models.JSONField(default=dict, blank=True)

    # Tracing
    correlation_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status transition rules (overrideable)
    STATUS_TRANSITIONS = {
        'created': ['queued'],
        'queued': ['running', 'canceled'],
        'running': ['succeeded', 'failed', 'retry_scheduled', 'canceled'],
        'retry_scheduled': ['queued', 'dlq', 'canceled'],
    }

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "next_attempt_at"]),  # For scheduler polling
            models.Index(fields=["lease_expires_at"]),           # For lease stealing
            models.Index(fields=["correlation_id"]),             # For tracing
        ]

    def __str__(self):
        return f"{self.topic} ({self.id}) - {self.status}"

    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new_status is valid. Override to customize."""
        valid_next = self.STATUS_TRANSITIONS.get(self.status, [])
        return new_status in valid_next or not self.STATUS_TRANSITIONS

    def transition_to(self, new_status: str, result: dict = None, error: dict = None) -> bool:
        """Transition to new status if valid."""
        old_status = self.status
        if not self.can_transition_to(new_status):
            return False

        self.status = new_status
        if result:
            self.result_summary = result
        if error:
            self.error_redacted = error
        self.save()
        self.on_status_change(old_status, new_status)
        return True

    def on_status_change(self, old_status: str, new_status: str):
        """Called when status changes. Override to add custom behavior."""
        pass

    def enqueue(self):
        """Enqueue job for processing."""
        self.transition_to('queued')

    def start(self, worker_id: str, lease_seconds: int = 300):
        """Mark job as started by worker."""
        self.lease_owner = worker_id
        self.lease_expires_at = timezone.now() + timezone.timedelta(seconds=lease_seconds)
        self.transition_to('running')

    def complete(self, result: dict = None):
        """Mark job as completed."""
        self.transition_to('succeeded', result=result)

    def fail(self, error: dict):
        """Mark job as failed."""
        if self.attempts >= self.max_attempts:
            self.transition_to('dlq', error=error)
        else:
            self.attempts += 1
            self.transition_to('retry_scheduled', error=error)

    def cancel(self):
        """Cancel job."""
        self.transition_to('canceled')

    def heartbeat(self, lease_seconds: int = 300):
        """Update heartbeat and extend lease."""
        self.heartbeat_at = timezone.now()
        self.lease_expires_at = timezone.now() + timezone.timedelta(seconds=lease_seconds)
        self.save(update_fields=['heartbeat_at', 'lease_expires_at'])



class JobEventTypeChoices(models.TextChoices):
    PROGRESS = "progress", _("Progress")
    LOG = "log", _("Log")
    ARTIFACT = "artifact", _("Artifact")
    FINAL = "final", _("Final Status")
    ERROR = "error", _("Error")


class JobEvent(models.Model):
    """
    Portable event stream for jobs.
    Enables SSE and timeline views regardless of backend.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="events")

    seq = models.IntegerField(help_text="Monotonic sequence number for this job")
    type = models.CharField(max_length=50, choices=JobEventTypeChoices.choices)

    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["job", "seq"]
        unique_together = ["job", "seq"]

    def __str__(self):
        return f"{self.job.id} #{self.seq} {self.type}"

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from .contracts import ModalTaskType

class ModalProviderConfig(models.Model):
    """
    Configuration for a provider (e.g., OpenAI, ElevenLabs).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    provider_key = models.CharField(max_length=100, help_text="Key from the ProviderRegistry")
    config = models.JSONField(
        default=dict, 
        blank=True,
        help_text="JSON config matching provider schema. Secrets should use SecretRef (env://...)"
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.provider_key})"


class ModalEndpoint(models.Model):
    """
    A specific capability endpoint exposed to consumers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, help_text="URL slug for this endpoint (e.g. 'company-chat')")
    name = models.CharField(max_length=255)
    
    provider_config = models.ForeignKey(ModalProviderConfig, on_delete=models.CASCADE, related_name='endpoints')
    
    # Simple list of allowed tasks for this endpoint
    allowed_task_types = models.JSONField(
        default=list, 
        help_text="List of allowed ModalTaskType strings"
    )
    
    default_params = models.JSONField(
        default=dict, blank=True,
        help_text="Default parameters injected into requests (e.g. model='gpt-4', voice_id='...')"
    )
    
    access_policy = models.JSONField(
        default=dict, blank=True,
        help_text="RBAC policy: allowed_groups, allowed_users, etc."
    )
    
    rate_limit = models.JSONField(default=dict, blank=True)
    budget_policy = models.JSONField(default=dict, blank=True)
    
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug


class ModalJob(models.Model):
    """
    Tracks asynchronous execution of modal tasks.
    """
    class State(models.TextChoices):
        QUEUED = 'queued', _('Queued')
        RUNNING = 'running', _('Running')
        SUCCEEDED = 'succeeded', _('Succeeded')
        FAILED = 'failed', _('Failed')
        CANCELED = 'canceled', _('Canceled')
        DLQ = 'dlq', _('Dead Letter Queue')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4) # External ref
    correlation_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    endpoint = models.ForeignKey(ModalEndpoint, on_delete=models.CASCADE, related_name='jobs')
    task_type = models.CharField(max_length=100)
    
    state = models.CharField(max_length=20, choices=State.choices, default=State.QUEUED, db_index=True)
    
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # Payloads (Redacted)
    payload_redacted = models.JSONField(default=dict, blank=True)
    result_summary = models.JSONField(default=dict, blank=True)
    error_redacted = models.TextField(blank=True)
    
    worker_meta = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['state', 'scheduled_at']),
        ]

    def __str__(self):
        return f"{self.job_id} ({self.state})"


class ModalArtifact(models.Model):
    """
    Reference to a file generated or used by a job.
    Linked to a Job or just standalone.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(ModalJob, on_delete=models.SET_NULL, null=True, blank=True, related_name='artifacts')
    
    kind = models.CharField(max_length=50) # text, audio, image, video, json
    uri = models.CharField(max_length=1024) # blob://... or s3://...
    mime = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True)
    
    meta = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.kind} - {self.uri}"


class ModalAuditEvent(models.Model):
    """
    Audit log for compliance and debugging.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_id = models.CharField(max_length=100, null=True, blank=True)
    
    action = models.CharField(max_length=100) # config.create, run.execute, etc.
    target_type = models.CharField(max_length=50) # endpoint, job, etc.
    target_id = models.CharField(max_length=100, null=True, blank=True)
    
    correlation_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

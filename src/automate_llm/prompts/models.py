import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class PromptStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    REVIEW = "review", _("Review")
    APPROVED = "approved", _("Approved")
    RELEASED = "released", _("Released")
    DEPRECATED = "deprecated", _("Deprecated")
    REVOKED = "revoked", _("Revoked")

class Prompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    key = models.SlugField(max_length=255, help_text="Stable key e.g. invoice.extract.v1")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant_id", "key")]

    def __str__(self):
        return f"{self.key} ({self.tenant_id})"

class PromptVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=PromptStatus.choices,
        default=PromptStatus.DRAFT
    )

    # Content
    system_template = models.TextField(blank=True, help_text="Jinja2 system message template")
    user_template = models.TextField(blank=True, help_text="Jinja2 user message template")
    few_shots = models.JSONField(default=list, blank=True)

    # Schemas & Policy
    variables_schema = models.JSONField(default=dict, blank=True) # JSON Schema for inputs
    output_schema = models.JSONField(default=dict, blank=True) # JSON Schema for response
    tool_policy = models.JSONField(default=dict, blank=True) # Allowlist etc.
    model_defaults = models.JSONField(default=dict, blank=True) # temperature, etc.

    # Audit
    content_hash = models.CharField(max_length=64, blank=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    change_log = models.TextField(blank=True)

    class Meta:
        unique_together = [("prompt", "version")]
        ordering = ["-version"]

    def __str__(self):
        return f"{self.prompt.key} v{self.version}"

class PromptRelease(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name="releases")
    channel = models.CharField(max_length=50, default="prod", db_index=True) # dev, staging, prod
    active_version = models.ForeignKey(PromptVersion, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)
    released_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = [("prompt", "channel")]

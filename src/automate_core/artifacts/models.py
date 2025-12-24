import uuid

from django.db import models

from ..executions.models import Execution, StepRun


class Artifact(models.Model):
    """
    Blob reference for large outputs (files, audio, expensive JSON).
    Content-addressed immutable usage.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)

    execution = models.ForeignKey(Execution, related_name="artifacts", on_delete=models.CASCADE)
    step_run = models.ForeignKey(StepRun, related_name="artifacts", on_delete=models.SET_NULL, null=True, blank=True)

    kind = models.CharField(
        max_length=32,
        choices=[
            ("text", "Text"),
            ("json", "JSON"),
            ("audio", "Audio"),
            ("video", "Video"),
            ("image", "Image"),
            ("file", "File"),
        ],
    )

    uri = models.CharField(max_length=1024, help_text="s3:// or file:// URI")
    mime_type = models.CharField(max_length=128, default="application/octet-stream")
    size_bytes = models.BigIntegerField(default=0)

    # Integrity
    sha256 = models.CharField(max_length=64, db_index=True)

    # Metadata
    meta = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Retention policy

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "execution"]),
            models.Index(fields=["sha256"]),
        ]

    def __str__(self):
        return f"{self.kind} ({self.size_bytes}b) @ {self.uri}"

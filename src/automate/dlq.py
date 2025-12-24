import uuid

from django.db import models

from .models import Execution


class DeadLetter(models.Model):
    """
    Holds failed executions that have exhausted retries.
    Track B: "Dead Letter Queue specialized model"
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    execution = models.OneToOneField(
        Execution, on_delete=models.CASCADE, related_name="dead_letter", null=True, blank=True
    )
    from .outbox import Outbox  # noqa: PLC0415

    outbox = models.OneToOneField(Outbox, on_delete=models.CASCADE, related_name="dead_letter", null=True, blank=True)

    # Reason for failure (Category)
    reason_code = models.CharField(max_length=50, default="unknown", db_index=True)
    # e.g. 'timeout', 'auth_error', 'rate_limit', 'crash'

    last_error_redacted = models.TextField()

    replay_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DLQ {self.id} (Exec {self.execution_id})"

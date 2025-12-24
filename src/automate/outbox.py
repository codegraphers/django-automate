import uuid
from django.db import models
from django.utils import timezone
from .models import Event

class OutboxStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    LOCKED = "locked", "Locked"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"
    DEAD = "dead", "Dead"

class Outbox(models.Model):
    """
    Transactional outbox for Events. 
    Events are written here in the same transaction as the business data change.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="outbox_entry")
    
    status = models.CharField(
        max_length=20, 
        choices=OutboxStatusChoices.choices, 
        default=OutboxStatusChoices.PENDING,
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Concurrency & Reliability
    locked_at = models.DateTimeField(null=True, blank=True)
    lock_owner = models.CharField(max_length=255, null=True, blank=True)
    attempts = models.IntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "Outbox entries"

    def __str__(self):
        return f"Outbox {self.id} (Event {self.event_id})"

# Outbox Pattern Reference

The Outbox Pattern provides reliable async processing with transactional guarantees. This is the foundation for all background job processing in Django Automate.

## Overview

The pattern ensures:
- **Atomicity**: Work items are created in the same transaction as business data
- **At-least-once delivery**: Items are retried until successful
- **Ordering**: Items are processed in next_attempt_at order
- **Crash recovery**: Stuck items are automatically reaped

## Components

### OutboxItem Model

```python
from automate_core.outbox.models import OutboxItem

class OutboxItem(models.Model):
    """Represents a work item in the outbox."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING'   # Ready for processing
        RUNNING = 'RUNNING'   # Currently being processed
        RETRY = 'RETRY'       # Failed, will retry
        COMPLETED = 'COMPLETED'
        FAILED = 'FAILED'     # Permanent failure
    
    id = models.UUIDField(primary_key=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    payload = models.JSONField()
    
    # Retry tracking
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    next_attempt_at = models.DateTimeField()
    last_error = models.TextField(blank=True)
    
    # Lease for exclusive claiming
    lease_owner = models.CharField(max_length=255, blank=True)
    lease_expires_at = models.DateTimeField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Status Lifecycle

```
PENDING → RUNNING → COMPLETED
    ↓         ↓
  RETRY ←─────┘
    ↓
  FAILED (after max_attempts)
```

---

## Claiming Items

### SkipLockedClaimOutboxStore (PostgreSQL/MySQL)

High-performance claiming using `SELECT ... FOR UPDATE SKIP LOCKED`.

```python
from automate_core.outbox.store import SkipLockedClaimOutboxStore

store = SkipLockedClaimOutboxStore(lease_seconds=300)

# Claim up to 10 items
items = store.claim_batch("worker-123", limit=10)

for item in items:
    print(f"Processing {item.id}")
```

### OptimisticClaimOutboxStore (SQLite)

For databases without `SKIP LOCKED` support.

```python
from automate_core.outbox.store import OptimisticClaimOutboxStore

store = OptimisticClaimOutboxStore(lease_seconds=300)
items = store.claim_batch("worker-123", limit=10)
```

---

## Processing Items

### Success

```python
store.mark_success(item.id, "worker-123")
# Status → COMPLETED
```

### Retry (Transient Errors)

```python
from datetime import timedelta
from django.utils import timezone

next_attempt = timezone.now() + timedelta(minutes=5)
store.mark_retry(item.id, "worker-123", next_attempt, "API timeout")
# Status → RETRY, attempt_count += 1
```

### Failure (Permanent Errors)

```python
store.mark_failed(item.id, "worker-123", "Invalid payload: missing required field")
# Status → FAILED
```

---

## Reaper: Recovering Stuck Items

The `OutboxReaper` recovers items that are stuck in RUNNING state (worker crashed).

```python
from automate_core.outbox.reaper import OutboxReaper

# Reap items stuck for over 10 minutes
reaper = OutboxReaper(stale_threshold_seconds=600)
reaped_count = reaper.reap_stale_items()

print(f"Recovered {reaped_count} stuck items")
```

### Scheduling

Run the reaper periodically via cron or Celery beat:

```python
# Celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'reap-stuck-outbox': {
        'task': 'automate_core.tasks.reap_outbox',
        'schedule': 300.0,  # Every 5 minutes
    },
}
```

Or via management command:

```bash
python manage.py outbox_reap
```

---

## Custom Store Implementation

```python
from automate_core.outbox.store import BaseOutboxStore

class MyCustomStore(BaseOutboxStore):
    """Custom store with Redis-backed claiming."""
    
    def claim_batch(self, worker_id: str, limit: int) -> list[OutboxItem]:
        # Custom claiming logic
        pass
    
    def mark_success(self, item_id: UUID, worker_id: str) -> None:
        # Custom success handling
        pass
    
    def mark_retry(self, item_id: UUID, worker_id: str, 
                   next_attempt: datetime, error: str) -> None:
        # Custom retry handling
        pass
    
    def mark_failed(self, item_id: UUID, worker_id: str, error: str) -> None:
        # Custom failure handling
        pass
```

---

## Complete Worker Example

```python
import time
from django.utils import timezone
from datetime import timedelta

from automate_core.outbox.store import SkipLockedClaimOutboxStore


def run_worker(worker_id: str):
    """Simple outbox worker loop."""
    store = SkipLockedClaimOutboxStore(lease_seconds=300)
    
    while True:
        items = store.claim_batch(worker_id, limit=10)
        
        if not items:
            time.sleep(1)
            continue
        
        for item in items:
            try:
                # Process the item
                result = process_item(item.payload)
                store.mark_success(item.id, worker_id)
                
            except TransientError as e:
                # Retry with exponential backoff
                delay = min(300, 30 * (2 ** item.attempt_count))
                next_attempt = timezone.now() + timedelta(seconds=delay)
                store.mark_retry(item.id, worker_id, next_attempt, str(e))
                
            except PermanentError as e:
                # No retry
                store.mark_failed(item.id, worker_id, str(e))


def process_item(payload: dict) -> dict:
    """Your processing logic here."""
    pass
```

---

## Configuration

```python
# settings.py
AUTOMATE_OUTBOX = {
    # Default lease duration
    'LEASE_SECONDS': 300,
    
    # Reaper configuration
    'REAPER_STALE_THRESHOLD': 600,
    
    # Store selection
    'STORE_BACKEND': 'automate_core.outbox.store.SkipLockedClaimOutboxStore',
    
    # Retry configuration
    'MAX_ATTEMPTS': 5,
    'RETRY_BACKOFF_MULTIPLIER': 2,
    'RETRY_BACKOFF_MAX': 3600,
}
```

## See Also

- [Extension Points](extension-points.md#outbox-pattern)
- [Microservices Deployment](../deployment/checklist.md)

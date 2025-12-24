import logging
from datetime import timedelta

from django.utils import timezone

from ..executions.models import Execution, ExecutionStatusChoices

logger = logging.getLogger(__name__)

class LeaseManager:
    """
    Distributed Locking Service for SRE-grade concurrency control.
    Uses DB "Lease" pattern: acquire, heartbeat, release, steal.
    """

    def __init__(self, worker_id: str):
        self.worker_id = worker_id

    def acquire_execution(self, execution_id: str, ttl_seconds: int = 60) -> bool:
        """
        Attempts to acquire lock on an execution.
        Must check: status is running/queued AND lease is expired.
        """
        now = timezone.now()
        expires_at = now + timedelta(seconds=ttl_seconds)

        # Atomic Update with optimistic concurrency
        updated = Execution.objects.filter(
            id=execution_id,
            # Condition: Unlocked OR Lease Expired
            lease_expires_at__lt=now # This covers locked-but-expired
        ).exclude(
            # Don't steal if I already own it (refresh instead)
            lease_owner=self.worker_id
        ).update(
            lease_owner=self.worker_id,
            lease_expires_at=expires_at,
            heartbeat_at=now
        )

        if updated:
             logger.info(f"Worker {self.worker_id} acquired execution {execution_id}")
             return True

        # Case: I already own it?
        # Or Case: Unlocked (null lease owner)?
        # The filter above (lease_expires_at__lt=now) implies it had an expiry set.
        # Handling the "fresh claim" (null owner) logic:
        updated_fresh = Execution.objects.filter(
            id=execution_id,
            lease_owner__isnull=True
        ).update(
            lease_owner=self.worker_id,
            lease_expires_at=expires_at,
            heartbeat_at=now,
            status=ExecutionStatusChoices.RUNNING # Auto-transition if needed
        )

        return updated_fresh > 0

    def heartbeat_execution(self, execution_id: str, ttl_seconds: int = 60) -> bool:
        """
        Extend the lease if I own it.
        """
        now = timezone.now()
        expires_at = now + timedelta(seconds=ttl_seconds)

        updated = Execution.objects.filter(
            id=execution_id,
            lease_owner=self.worker_id
        ).update(
            lease_expires_at=expires_at,
            heartbeat_at=now
        )
        return updated > 0

    def release_execution(self, execution_id: str):
        Execution.objects.filter(
            id=execution_id,
            lease_owner=self.worker_id
        ).update(
            lease_owner=None,
            lease_expires_at=None
        )

    # Note: Step run leases follow identical logic.
    # We could make this generic or just dup for clarity.

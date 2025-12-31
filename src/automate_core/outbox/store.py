from __future__ import annotations

from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import F, Q

from .interfaces import OutboxStore
from .models import OutboxItem


class SkipLockedClaimOutboxStore(OutboxStore):
    """
    Strategy for DBs supporting SKIP LOCKED (Postgres, MySQL 8+, Oracle).
    Uses select_for_update(skip_locked=True).
    """

    def __init__(self, lease_seconds: int = 60):
        self.lease_seconds = lease_seconds

    def claim_batch(self, owner: str, limit: int, now: datetime) -> list[OutboxItem]:
        """
        Claim a batch of items for processing.
        
        Claimable items are:
        1. PENDING/RETRY with next_attempt_at <= now
        2. RUNNING with lease_expires_at < now (stale - worker crashed)
        """
        lease_delta = timedelta(seconds=self.lease_seconds)

        with transaction.atomic():
            # Build query for claimable items:
            # - PENDING/RETRY that are due
            # - RUNNING with expired lease (stale)
            pending_or_retry = Q(status__in=["PENDING", "RETRY"], next_attempt_at__lte=now)
            stale_running = Q(status="RUNNING", lease_expires_at__lt=now)
            
            qs = (
                OutboxItem.objects.select_for_update(skip_locked=True)
                .filter(pending_or_retry | stale_running)
                .order_by("priority", "next_attempt_at", "id")[:limit]
            )

            items = list(qs)
            if not items:
                return []

            updated = []
            for item in items:
                item.status = "RUNNING"
                item.lease_owner = owner
                item.lease_expires_at = now + lease_delta
                item.save(update_fields=["status", "lease_owner", "lease_expires_at", "updated_at"])
                updated.append(item)

            return updated

    def mark_done(self, item_id: int, owner: str) -> None:
        OutboxItem.objects.filter(id=item_id, lease_owner=owner).update(
            status="DONE", lease_owner=None, lease_expires_at=None
        )

    def mark_retry(self, item_id: int, owner: str, next_attempt_at: datetime, error_code: str) -> None:
        OutboxItem.objects.filter(id=item_id, lease_owner=owner).update(
            status="RETRY",
            lease_owner=None,
            lease_expires_at=None,
            next_attempt_at=next_attempt_at,
            last_error_code=error_code,
            attempt_count=F("attempt_count") + 1,
        )

    def mark_dlq(self, item_id: int, owner: str, error_code: str) -> None:
        OutboxItem.objects.filter(id=item_id, lease_owner=owner).update(
            status="DLQ", lease_owner=None, lease_expires_at=None, last_error_code=error_code
        )


class OptimisticLeaseOutboxStore(OutboxStore):
    """
    Strategy for DBs WITHOUT SKIP LOCKED (SQLite, Legacy).
    Uses atomic UPDATE WHERE lease is null logic.
    """

    def __init__(self, lease_seconds: int = 60):
        self.lease_seconds = lease_seconds

    def claim_batch(self, owner: str, limit: int, now: datetime) -> list[OutboxItem]:
        """
        Claim a batch of items for processing (optimistic locking for DBs without SKIP LOCKED).
        
        Claimable items are:
        1. PENDING/RETRY with next_attempt_at <= now (and no current lease)
        2. RUNNING with lease_expires_at < now (stale - worker crashed)
        """
        lease_expires = now + timedelta(seconds=self.lease_seconds)

        # Build query for claimable items
        pending_or_retry = Q(
            status__in=["PENDING", "RETRY"],
            next_attempt_at__lte=now,
            lease_owner__isnull=True,
        )
        stale_running = Q(status="RUNNING", lease_expires_at__lt=now)

        candidates = list(
            OutboxItem.objects.filter(pending_or_retry | stale_running)
            .values_list("id", flat=True)
            .order_by("priority", "next_attempt_at")[:limit]
        )

        if not candidates:
            return []

        # Claim attempts - use Q to match claimable conditions
        OutboxItem.objects.filter(
            Q(id__in=candidates) & (Q(lease_owner__isnull=True) | Q(lease_expires_at__lt=now))
        ).update(
            status="RUNNING", lease_owner=owner, lease_expires_at=lease_expires, updated_at=now
        )

        # Verify what we actually won
        return list(OutboxItem.objects.filter(id__in=candidates, lease_owner=owner))

    def mark_done(self, item_id: int, owner: str) -> None:
        SkipLockedClaimOutboxStore.mark_done(self, item_id, owner)

    def mark_retry(self, item_id: int, owner: str, next_attempt_at: datetime, error_code: str) -> None:
        SkipLockedClaimOutboxStore.mark_retry(self, item_id, owner, next_attempt_at, error_code)

    def mark_dlq(self, item_id: int, owner: str, error_code: str) -> None:
        SkipLockedClaimOutboxStore.mark_dlq(self, item_id, owner, error_code)

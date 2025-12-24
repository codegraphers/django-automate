from __future__ import annotations

from datetime import datetime, timedelta

from django.db import transaction

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
        lease_delta = timedelta(seconds=self.lease_seconds)

        with transaction.atomic():
            # Find candidates: PENDING or RETRY due now, or stale leases
            # Note: We prioritize PENDING/RETRY over stale claims usually,
            # but simplest query is finding anything claimable.

            qs = (
                OutboxItem.objects.select_for_update(skip_locked=True)
                .filter(status__in=["PENDING", "RETRY"], next_attempt_at__lte=now)
                .order_by("priority", "next_attempt_at", "id")[:limit]
            )

            # Also check for stale locks?
            # SKIP LOCKED with filters on lease_expires_at is tricky if mixed with status.
            # Simplified approach: Claim PENDING/RETRY first. Stale locks handled separately or strictly via updates.
            # For simplicity in this skeleton, we focus on PENDING/RETRY.

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
            attempt_count=models.F("attempt_count") + 1,
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
        lease_expires = now + timedelta(seconds=self.lease_seconds)

        # We can't select then update safely without locking the table (bad for concurrency).
        # Instead, try to UPDATE a batch of rows blindly, then SELECT what we won.
        # This is strictly "Optimistic Locking".

        # SQLite doesn't support UPDATE..LIMIT until recent versions (enabled in Django 4.2+ on some backends but not guaranteed).
        # We assume standard UPDATE ... LIMIT logic is available or we accept checking via a loop.

        # Strategy: Find IDs capable of being claimed (READ COMMITTED usually safe enough for candidate selection)
        candidates = list(
            OutboxItem.objects.filter(
                status__in=["PENDING", "RETRY"],
                next_attempt_at__lte=now,
                lease_owner__isnull=True,  # Simplified check
            )
            .values_list("id", flat=True)
            .order_by("priority", "next_attempt_at")[:limit]
        )

        if not candidates:
            return []

        # Claim attempts
        OutboxItem.objects.filter(id__in=candidates, lease_owner__isnull=True).update(
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

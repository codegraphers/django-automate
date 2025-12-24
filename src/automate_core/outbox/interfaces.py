from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .models import OutboxItem


class OutboxStore(ABC):
    """
    Strategy abstract class for claiming Outbox items.
    Implementations handle DB-specific locking logic (SKIP LOCKED vs Optimistic Lease).
    """

    @abstractmethod
    def claim_batch(self, owner: str, limit: int, now: datetime) -> list[OutboxItem]:
        """
        Claim up to `limit` pending/retry items for `owner`.
        Must set status='RUNNING', lease_owner=owner, lease_expires_at=now+lease_duration.
        """
        raise NotImplementedError

    @abstractmethod
    def mark_done(self, item_id: int, owner: str) -> None:
        """Mark item as DONE."""
        raise NotImplementedError

    @abstractmethod
    def mark_retry(self, item_id: int, owner: str, next_attempt_at: datetime, error_code: str) -> None:
        """Mark item as RETRY with new schedule and increment attempt_count."""
        raise NotImplementedError

    @abstractmethod
    def mark_dlq(self, item_id: int, owner: str, error_code: str) -> None:
        """Mark item as DLQ (Dead Letter Queue)."""
        raise NotImplementedError

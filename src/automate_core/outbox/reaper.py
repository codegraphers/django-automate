"""
Outbox Reaper - SRE-grade stuck item recovery.

Moves RUNNING items with expired leases back to RETRY status
so they can be picked up by workers again.

This handles the case where a worker crashes mid-processing
and doesn't release its lease.

Usage:
    python manage.py outbox_reap
    
Or programmatically:
    from automate_core.outbox.reaper import OutboxReaper
    reaper = OutboxReaper()
    reaped_count = reaper.reap_stale_items()
"""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import OutboxItem

logger = logging.getLogger(__name__)


class OutboxReaper:
    """
    Recovers stuck RUNNING items whose leases have expired.
    
    SRE Pattern: Reaper runs periodically (cron/celery beat) to prevent
    items from being stuck forever after worker crashes.
    """

    def __init__(
        self,
        stale_threshold_seconds: int = 300,
        max_reap_batch: int = 100,
        retry_delay_seconds: int = 60,
    ):
        """
        Args:
            stale_threshold_seconds: How long after lease expiry to consider stale (default: 5 min)
            max_reap_batch: Maximum items to reap per invocation (default: 100)
            retry_delay_seconds: How long before reaped items should be retried (default: 1 min)
        """
        self.stale_threshold_seconds = stale_threshold_seconds
        self.max_reap_batch = max_reap_batch
        self.retry_delay_seconds = retry_delay_seconds

    def reap_stale_items(self) -> int:
        """
        Find and recover stuck RUNNING items.
        
        Returns:
            Number of items reaped.
        """
        now = timezone.now()
        stale_cutoff = now - timedelta(seconds=self.stale_threshold_seconds)
        next_attempt = now + timedelta(seconds=self.retry_delay_seconds)

        with transaction.atomic():
            # Find stale RUNNING items
            stale_items = list(
                OutboxItem.objects.select_for_update(skip_locked=True)
                .filter(
                    status="RUNNING",
                    lease_expires_at__lt=stale_cutoff,
                )
                .order_by("lease_expires_at")[:self.max_reap_batch]
            )

            if not stale_items:
                return 0

            reaped_count = 0
            for item in stale_items:
                old_owner = item.lease_owner

                # Move back to RETRY with scheduled next attempt
                item.status = "RETRY"
                item.lease_owner = None
                item.lease_expires_at = None
                item.next_attempt_at = next_attempt
                item.last_error_code = f"REAPED:stale_lease:{old_owner}"
                item.save(update_fields=[
                    "status", "lease_owner", "lease_expires_at",
                    "next_attempt_at", "last_error_code", "updated_at"
                ])

                logger.warning(
                    f"Reaped stale outbox item {item.id} "
                    f"(kind={item.kind}, old_owner={old_owner})"
                )
                reaped_count += 1

            return reaped_count

    def get_stale_count(self) -> int:
        """Get count of items that would be reaped (for monitoring)."""
        stale_cutoff = timezone.now() - timedelta(seconds=self.stale_threshold_seconds)
        return OutboxItem.objects.filter(
            status="RUNNING",
            lease_expires_at__lt=stale_cutoff,
        ).count()

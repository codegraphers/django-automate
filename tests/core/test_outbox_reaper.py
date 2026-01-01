"""
Tests for outbox reaper functionality.

Verifies that stuck RUNNING items can be recovered.
"""

import pytest
from datetime import timedelta
from django.utils import timezone

from automate_core.outbox.models import OutboxItem
from automate_core.outbox.reaper import OutboxReaper
from automate_core.outbox.store import SkipLockedClaimOutboxStore


@pytest.mark.django_db
class TestOutboxReaper:
    """Test the OutboxReaper recovers stuck items."""

    def test_reap_stale_running_item(self):
        """Stale RUNNING items should be moved to RETRY."""
        # Create a stuck item with expired lease
        expired_time = timezone.now() - timedelta(minutes=10)
        item = OutboxItem.objects.create(
            kind="test.stuck",
            payload={"test": True},
            status="RUNNING",
            lease_owner="dead-worker",
            lease_expires_at=expired_time,
            attempt_count=1,
        )
        
        reaper = OutboxReaper(stale_threshold_seconds=60)  # 1 minute threshold
        reaped_count = reaper.reap_stale_items()
        
        assert reaped_count == 1
        
        item.refresh_from_db()
        assert item.status == "RETRY"
        assert item.lease_owner is None
        assert item.next_attempt_at is not None
        assert "REAPED" in item.last_error_code

    def test_reap_does_not_touch_fresh_running(self):
        """Fresh RUNNING items should not be reaped."""
        # Create an item with non-expired lease
        future_time = timezone.now() + timedelta(minutes=5)
        item = OutboxItem.objects.create(
            kind="test.active",
            payload={},
            status="RUNNING",
            lease_owner="active-worker",
            lease_expires_at=future_time,
        )
        
        reaper = OutboxReaper(stale_threshold_seconds=60)
        reaped_count = reaper.reap_stale_items()
        
        assert reaped_count == 0
        
        item.refresh_from_db()
        assert item.status == "RUNNING"
        assert item.lease_owner == "active-worker"

    def test_reap_respects_max_batch(self):
        """Reaper should respect max_reap_batch limit."""
        expired_time = timezone.now() - timedelta(minutes=10)
        
        # Create 5 stale items
        for i in range(5):
            OutboxItem.objects.create(
                kind=f"test.stale_{i}",
                payload={},
                status="RUNNING",
                lease_owner="dead-worker",
                lease_expires_at=expired_time,
            )
        
        reaper = OutboxReaper(stale_threshold_seconds=60, max_reap_batch=2)
        reaped_count = reaper.reap_stale_items()
        
        assert reaped_count == 2
        
        # 3 should still be RUNNING
        remaining = OutboxItem.objects.filter(status="RUNNING").count()
        assert remaining == 3

    def test_reaped_item_is_claimable(self):
        """After reaping, item should be claimable by workers."""
        expired_time = timezone.now() - timedelta(minutes=10)
        item = OutboxItem.objects.create(
            kind="test.stuck_claimable",
            payload={},
            status="RUNNING",
            lease_owner="crashed-worker",
            lease_expires_at=expired_time,
            next_attempt_at=expired_time,
        )
        
        # Reap the item
        reaper = OutboxReaper(stale_threshold_seconds=60, retry_delay_seconds=0)
        reaper.reap_stale_items()
        
        item.refresh_from_db()
        assert item.status == "RETRY"
        
        # Now it should be claimable
        store = SkipLockedClaimOutboxStore(lease_seconds=60)
        claimed = store.claim_batch("new-worker", limit=10, now=timezone.now())
        
        assert len(claimed) == 1
        assert claimed[0].id == item.id

    def test_get_stale_count(self):
        """get_stale_count should return accurate count for monitoring."""
        expired_time = timezone.now() - timedelta(minutes=10)
        future_time = timezone.now() + timedelta(minutes=10)
        
        # Create 2 stale and 1 fresh
        for i in range(2):
            OutboxItem.objects.create(
                kind=f"test.stale_{i}",
                payload={},
                status="RUNNING",
                lease_expires_at=expired_time,
            )
        OutboxItem.objects.create(
            kind="test.fresh",
            payload={},
            status="RUNNING",
            lease_expires_at=future_time,
        )
        
        reaper = OutboxReaper(stale_threshold_seconds=60)
        count = reaper.get_stale_count()
        
        assert count == 2

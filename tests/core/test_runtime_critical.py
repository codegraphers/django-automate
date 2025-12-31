"""
Unit tests for runtime-critical Job operations.

These tests verify that core reliability paths don't crash:
- Job.start() - uses timedelta for lease calculation
- Job.heartbeat() - uses timedelta for lease extension
- Outbox mark_retry() - uses F() for atomic increment

Related to: PR-03 Runtime Crash Fixes
"""

import pytest
from datetime import timedelta
from django.utils import timezone

from automate_core.jobs.models import Job, JobStatusChoices
from automate_core.outbox.models import OutboxItem
from automate_core.outbox.store import SkipLockedClaimOutboxStore


@pytest.mark.django_db
class TestJobLeaseOperations:
    """Test Job lease and heartbeat operations that use timedelta."""

    def test_job_start_sets_lease(self):
        """Job.start() should set lease_owner and lease_expires_at without crashing."""
        job = Job.objects.create(
            topic="test.job",
            kind="custom",
            status=JobStatusChoices.QUEUED,
        )
        
        # This would crash if timezone.timedelta was used (it doesn't exist)
        job.start(worker_id="test-worker-1", lease_seconds=300)
        
        job.refresh_from_db()
        assert job.lease_owner == "test-worker-1"
        assert job.lease_expires_at is not None
        assert job.status == JobStatusChoices.RUNNING

    def test_job_heartbeat_extends_lease(self):
        """Job.heartbeat() should extend lease without crashing."""
        job = Job.objects.create(
            topic="test.job",
            kind="custom",
            status=JobStatusChoices.RUNNING,
            lease_owner="test-worker-1",
            lease_expires_at=timezone.now() + timedelta(seconds=60),
        )
        
        original_expires = job.lease_expires_at
        
        # This would crash if timezone.timedelta was used
        job.heartbeat(lease_seconds=600)
        
        job.refresh_from_db()
        assert job.heartbeat_at is not None
        assert job.lease_expires_at > original_expires

    def test_job_start_with_custom_lease(self):
        """Job.start() should accept custom lease duration."""
        job = Job.objects.create(
            topic="test.custom_lease",
            kind="custom",
            status=JobStatusChoices.QUEUED,
        )
        
        before_start = timezone.now()
        job.start(worker_id="worker-2", lease_seconds=1800)  # 30 minutes
        
        job.refresh_from_db()
        # Lease should be ~30 minutes from now
        expected_min = before_start + timedelta(seconds=1790)
        assert job.lease_expires_at >= expected_min


@pytest.mark.django_db
class TestOutboxRetryOperations:
    """Test Outbox retry operations that use F() for atomic increment."""

    def test_mark_retry_increments_attempt_count(self):
        """mark_retry() should atomically increment attempt_count without crashing."""
        item = OutboxItem.objects.create(
            kind="test.item",
            payload={"test": True},
            status="RUNNING",
            lease_owner="test-worker",
            attempt_count=1,
        )
        
        store = SkipLockedClaimOutboxStore(lease_seconds=60)
        next_attempt = timezone.now() + timedelta(seconds=60)
        
        # This would crash if models.F was used without importing F
        store.mark_retry(item.id, "test-worker", next_attempt, "TRANSIENT_ERROR")
        
        item.refresh_from_db()
        assert item.status == "RETRY"
        assert item.attempt_count == 2
        assert item.last_error_code == "TRANSIENT_ERROR"
        assert item.lease_owner is None

    def test_mark_retry_multiple_times(self):
        """mark_retry() should correctly increment count multiple times."""
        item = OutboxItem.objects.create(
            kind="test.multi_retry",
            payload={},
            status="RUNNING",
            lease_owner="worker-a",
            attempt_count=0,
        )
        
        store = SkipLockedClaimOutboxStore()
        
        # First retry
        item.status = "RUNNING"
        item.lease_owner = "worker-a"
        item.save()
        store.mark_retry(item.id, "worker-a", timezone.now() + timedelta(seconds=10), "ERR1")
        item.refresh_from_db()
        assert item.attempt_count == 1
        
        # Second retry (simulate re-claim)
        item.status = "RUNNING"
        item.lease_owner = "worker-b"
        item.save()
        store.mark_retry(item.id, "worker-b", timezone.now() + timedelta(seconds=20), "ERR2")
        item.refresh_from_db()
        assert item.attempt_count == 2


@pytest.mark.django_db
class TestOutboxStaleLeaseClaim:
    """Test that stale RUNNING items can be reclaimed."""

    def test_claim_stale_running_item(self):
        """Items stuck in RUNNING with expired lease should be claimable."""
        # Create an item that's been "stuck" - RUNNING with expired lease
        expired_time = timezone.now() - timedelta(minutes=5)
        item = OutboxItem.objects.create(
            kind="test.stale",
            payload={},
            status="RUNNING",
            lease_owner="dead-worker",
            lease_expires_at=expired_time,
            next_attempt_at=expired_time,
        )
        
        store = SkipLockedClaimOutboxStore(lease_seconds=60)
        now = timezone.now()
        
        # Should claim the stale item
        claimed = store.claim_batch("new-worker", limit=10, now=now)
        
        assert len(claimed) == 1
        assert claimed[0].id == item.id
        assert claimed[0].lease_owner == "new-worker"

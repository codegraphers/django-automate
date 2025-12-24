import datetime

import pytest
from django.utils import timezone

from automate.dispatcher import LOCK_TTL, Dispatcher
from automate.ingestion import EventIngestionService
from automate.models import Automation, Outbox, OutboxStatusChoices, TriggerSpec, TriggerTypeChoices


@pytest.mark.django_db
def test_lock_stealing():
    """
    P0 Test: Verify old LOCKED items are reclaimed (Stealing).
    """
    # 1. Setup
    auto = Automation.objects.create(name="Steal Test", slug="steal-test")
    TriggerSpec.objects.create(automation=auto, type=TriggerTypeChoices.MANUAL, filter_config={})

    event = EventIngestionService.ingest_event("manual", "test", {})
    entry = Outbox.objects.filter(payload__event_id=str(event.id)).first()
    assert entry is not None

    # 2. Simulate Abandoned Lock
    entry.status = OutboxStatusChoices.RUNNING
    entry.lease_owner = "dead-worker"
    # Set to past (expired)
    entry.lease_expires_at = timezone.now() - datetime.timedelta(seconds=LOCK_TTL + 10)
    entry.save()

    # 3. New Dispatcher
    dispatcher = Dispatcher()
    worker_id = "live-worker"

    # Fetch candidates should pick it up
    candidates = dispatcher._fetch_candidates(10, worker_id)

    assert entry in candidates

    entry.refresh_from_db()
    assert entry.status == OutboxStatusChoices.RUNNING
    assert entry.lease_owner == worker_id
    # Assert locked_at is fresh
    assert entry.lease_expires_at > timezone.now() - datetime.timedelta(seconds=5)

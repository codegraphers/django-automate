import pytest
from django.utils import timezone
import datetime
from automate.models import Event, Automation, TriggerSpec, TriggerTypeChoices, Outbox, OutboxStatusChoices
from automate.dispatcher import Dispatcher, LOCK_TTL
from automate.ingestion import EventIngestionService

@pytest.mark.django_db
def test_lock_stealing():
    """
    P0 Test: Verify old LOCKED items are reclaimed (Stealing).
    """
    # 1. Setup
    auto = Automation.objects.create(name="Steal Test", slug="steal-test")
    TriggerSpec.objects.create(automation=auto, type=TriggerTypeChoices.MANUAL, config={})
    
    event = EventIngestionService.ingest_event("manual", "test", {})
    entry = Outbox.objects.get(event=event)
    
    # 2. Simulate Abandoned Lock
    entry.status = OutboxStatusChoices.LOCKED
    entry.lock_owner = "dead-worker"
    # Set to past (expired)
    entry.locked_at = timezone.now() - datetime.timedelta(seconds=LOCK_TTL + 10)
    entry.save()
    
    # 3. New Dispatcher
    dispatcher = Dispatcher()
    worker_id = "live-worker"
    
    # Fetch candidates should pick it up
    candidates = dispatcher._fetch_candidates(10, worker_id)
    
    assert entry in candidates
    
    entry.refresh_from_db()
    assert entry.status == OutboxStatusChoices.LOCKED
    assert entry.lock_owner == worker_id
    # Assert locked_at is fresh
    assert entry.locked_at > timezone.now() - datetime.timedelta(seconds=5)

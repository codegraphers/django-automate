import pytest
from unittest.mock import patch
from django.utils import timezone
import datetime
from automate.models import Event, Automation, TriggerSpec, TriggerTypeChoices, Outbox, OutboxStatusChoices
from automate.dispatcher import Dispatcher
from automate.ingestion import EventIngestionService
from automate.dlq import DeadLetter

@pytest.mark.django_db
def test_dispatcher_retry_logic():
    """
    P0.3: Verify retry scheduling and DLQ promotion.
    """
    # 1. Setup
    auto = Automation.objects.create(name="Retry Test", slug="retry-test")
    TriggerSpec.objects.create(automation=auto, type=TriggerTypeChoices.MANUAL, config={})
    
    event = EventIngestionService.ingest_event("manual", "test", {})
    entry = Outbox.objects.get(event=event)
    
    dispatcher = Dispatcher()
    
    # 2. Mock Failure
    # We patch TriggerMatchingService to raise an exception
    with patch("automate.services.trigger.TriggerMatchingService.matches", side_effect=Exception("Simulated Failure")):
        
        # Attempt 1
        dispatcher.dispatch_batch()
        entry.refresh_from_db()
        assert entry.status == OutboxStatusChoices.FAILED
        assert entry.attempts == 1
        assert entry.next_attempt_at > timezone.now()
        
        # Attempt 2 (Too early - shouldn't be picked up)
        picked = dispatcher._fetch_candidates(10, "worker")
        assert entry not in picked
        
        # Move time forward
        future = timezone.now() + datetime.timedelta(seconds=10)
        with patch("django.utils.timezone.now", return_value=future):
            
            # Attempt 2 (Should be picked up)
            # Note: _fetch_candidates uses DB time usually, checking if logic uses timezone.now() in query?
            # It uses `now = timezone.now()` in Python, then filters.
            # So patching timezone.now() works for the filter query construction.
            
            dispatcher.dispatch_batch()
            entry.refresh_from_db()
            assert entry.attempts == 2
            
            # Attempt 3 (Max Retries = 3 default)
            # Need to force next attempt time again
            entry.next_attempt_at = future # allow immediate pickup for test speed
            entry.save()
            
            dispatcher.dispatch_batch()
            entry.refresh_from_db()
            assert entry.attempts == 3
            # If max=3, attempts=3 failure -> DEAD? Or check >= max?
            # Code: if entry.attempts >= MAX_RETRIES: mark DEAD.
            # Attempts starts at 0.
            # 1st run: fail -> attempts=1.
            # 2nd run: fail -> attempts=2.
            # 3rd run: fail -> attempts=3 -> attempts >= 3? YES.
            # So after 3rd failure, it goes DEAD.
            
            assert entry.status == OutboxStatusChoices.DEAD
            
            # Verify DLQ
            dlq = DeadLetter.objects.get(outbox=entry)
            assert "Simulated Failure" in dlq.last_error_redacted

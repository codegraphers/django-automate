import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from automate.dispatcher import Dispatcher
from automate.dlq import DeadLetter
from automate.ingestion import EventIngestionService
from automate.models import Automation, Outbox, OutboxStatusChoices, TriggerSpec, TriggerTypeChoices


@pytest.mark.django_db
def test_dispatcher_retry_logic():
    """
    P0.3: Verify retry scheduling and DLQ promotion.
    """
    # 1. Setup
    auto = Automation.objects.create(name="Retry Test", slug="retry-test")
    TriggerSpec.objects.create(automation=auto, type=TriggerTypeChoices.MANUAL, filter_config={})

    event = EventIngestionService.ingest_event("manual", "test", {})
    # Query by payload
    entry = Outbox.objects.filter(payload__event_id=str(event.id)).first()
    assert entry is not None

    dispatcher = Dispatcher()

    # 2. Mock Failure
    # We patch TriggerMatchingService to raise an exception
    with patch("automate.services.trigger.TriggerMatchingService.matches", side_effect=Exception("Simulated Failure")):

        # Attempt 1
        dispatcher.dispatch_batch()
        entry.refresh_from_db()
        assert entry.status == OutboxStatusChoices.RETRY
        assert entry.attempt_count == 1
        assert entry.next_attempt_at > timezone.now()

        # Attempt 2 (Too early - shouldn't be picked up)
        picked = dispatcher._fetch_candidates(10, "worker")
        assert entry not in picked

        # Move time forward
        future = timezone.now() + datetime.timedelta(seconds=10)
        with patch("django.utils.timezone.now", return_value=future):

            # Attempt 2 (Should be picked up)
            dispatcher.dispatch_batch()
            entry.refresh_from_db()
            assert entry.attempt_count == 2

            # Attempt 3 (Max Retries = 3 default)
            # Need to force next attempt time again
            entry.next_attempt_at = future - datetime.timedelta(seconds=1) # allow immediate pickup for test speed
            entry.save()

            dispatcher.dispatch_batch()
            entry.refresh_from_db()
            assert entry.attempt_count == 3
            # If max=3, attempts=3 failure -> DEAD.

            assert entry.status == OutboxStatusChoices.DLQ

            # Verify DLQ (via fields)
            # dlq = DeadLetter.objects.get(outbox=entry)
            assert "Simulated Failure" in entry.last_error_message

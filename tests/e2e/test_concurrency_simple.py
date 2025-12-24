import random
import threading
import time

import pytest
from django.db import connections

from automate.dispatcher import Dispatcher
from automate.ingestion import EventIngestionService
from automate.models import Automation, Outbox, OutboxStatusChoices, TriggerSpec, TriggerTypeChoices


@pytest.mark.django_db(transaction=True)
def test_outbox_concurrency():
    """
    P0 Test: Concurrency with 2 workers.
    """
    # Setup
    auto = Automation.objects.create(name="Concurrency Test", slug="concurrency-test")
    # Create dummy workflow to avoid warnings (and actually create executions if we checked for them)
    # But for this test, we just check Outbox -> DONE.
    from automate.models import Workflow
    Workflow.objects.create(automation=auto, version=1, is_live=True, graph={})

    # Ingest 50 events to ensure collision checking
    for i in range(50):
        EventIngestionService.ingest_event("manual", "test", {"i": i})

    assert Outbox.objects.count() == 50

    # Define Worker
    def worker(wid):
        # Clean connections for thread
        connections.close_all()
        dispatcher = Dispatcher()
        # Process until empty
        # dispatch_batch returns list of entries processed

        empty_retries = 10  # Retry a few times if we get empty result (transient lock)

        while True:
            processed = dispatcher.dispatch_batch(batch_size=5, worker_id=wid)
            if not processed:
                if empty_retries > 0:
                    empty_retries -= 1
                    time.sleep(random.uniform(0.1, 0.3))
                    continue
                break
            else:
                empty_retries = 10  # Reset on success

        connections.close_all()

    t1 = threading.Thread(target=worker, args=("worker-1",))
    t2 = threading.Thread(target=worker, args=("worker-2",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Assertions
    assert Outbox.objects.filter(status=OutboxStatusChoices.DONE).count() == 50
    assert Outbox.objects.filter(status=OutboxStatusChoices.RUNNING).count() == 0
    assert Outbox.objects.filter(status=OutboxStatusChoices.PENDING).count() == 0

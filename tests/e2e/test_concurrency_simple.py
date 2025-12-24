import pytest
import threading
from django.db import connections
from automate.models import Event, Outbox, OutboxStatusChoices, Automation, TriggerSpec, TriggerTypeChoices
from automate.ingestion import EventIngestionService
from automate.dispatcher import Dispatcher

@pytest.mark.django_db(transaction=True)
def test_outbox_concurrency():
    """
    P0 Test: Concurrency with 2 workers.
    """
    # Setup
    auto = Automation.objects.create(name="Concurrency Test", slug="concurrency-test")
    TriggerSpec.objects.create(automation=auto, type=TriggerTypeChoices.MANUAL, config={})
    
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
        while True:
            processed = dispatcher.dispatch_batch(batch_size=5, worker_id=wid)
            if not processed:
                # Check if any pending left?
                # It might be that other worker took them.
                # Just loop until DB really empty of pending?
                # Or simplistic check.
                break
        connections.close_all()
        
    t1 = threading.Thread(target=worker, args=("worker-1",))
    t2 = threading.Thread(target=worker, args=("worker-2",))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # Assertions
    assert Outbox.objects.filter(status=OutboxStatusChoices.PROCESSED).count() == 50
    assert Outbox.objects.filter(status=OutboxStatusChoices.LOCKED).count() == 0
    assert Outbox.objects.filter(status=OutboxStatusChoices.PENDING).count() == 0

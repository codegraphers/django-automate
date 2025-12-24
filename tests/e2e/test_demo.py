import pytest
from django.core.management import call_command
from automate.models import Event, Outbox, Execution, ExecutionStatusChoices, OutboxStatusChoices
from automate.dispatcher import Dispatcher
from automate.runtime import Runtime
from automate.ingestion import EventIngestionService

@pytest.mark.django_db
def test_demo_flow_e2e():
    """
    P0.7: Verify the demo flow works end-to-end.
    """
    # 1. Seed
    call_command("seed_demo")
    
    # 2. Trigger Manual Event
    event = EventIngestionService.ingest_event(
        event_type="manual",
        source="e2e",
        payload={"foo": "bar"}
    )
    
    # 3. Dispatch
    dispatcher = Dispatcher()
    dispatcher.dispatch_batch()
    
    outbox = Outbox.objects.get(event=event)
    assert outbox.status == OutboxStatusChoices.PROCESSED
    
    # 4. Verify Execution Created
    execution = Execution.objects.get(event=event)
    assert execution.status == ExecutionStatusChoices.QUEUED
    
    # 5. Runtime (simulate worker)
    runtime = Runtime()
    runtime.run_execution(execution.id)
    
    execution.refresh_from_db()
    assert execution.status == ExecutionStatusChoices.SUCCESS
    assert execution.steps.count() == 1
    step = execution.steps.first()
    assert step.step_id == "step1"
    assert step.status == ExecutionStatusChoices.SUCCESS

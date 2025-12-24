import pytest

from automate.dispatcher import Dispatcher
from automate.ingestion import EventIngestionService
from automate.models import Automation, Execution, TriggerSpec, TriggerTypeChoices, Workflow


@pytest.mark.django_db
def test_workflow_version_snapshot():
    """
    P0.2: Verify execution snapshots correct workflow version.
    """
    # 1. Setup Automation with 2 workflows
    auto = Automation.objects.create(name="Version Test", slug="version-test")

    # Workflow v1 (Live)
    wf1 = Workflow.objects.create(automation=auto, version=1, is_live=True, graph={})

    # Trigger
    TriggerSpec.objects.create(
        automation=auto,
        type=TriggerTypeChoices.MANUAL,
        filter_config={}
    )

    # 2. Ingest Event
    event = EventIngestionService.ingest_event(
        event_type="manual",
        source="test",
        payload={}
    )

    # 3. Dispatch
    dispatcher = Dispatcher()
    dispatcher.dispatch_batch()

    # 4. Assert v1
    execution = Execution.objects.get(event=event)
    assert execution.workflow_version == 1

    # 5. Add v2 (Not Live)
    wf2 = Workflow.objects.create(automation=auto, version=2, is_live=False, graph={})

    # Dispatch another event
    event2 = EventIngestionService.ingest_event(event_type="manual", source="test2", payload={})
    dispatcher.dispatch_batch()
    execution2 = Execution.objects.get(event=event2)
    assert execution2.workflow_version == 1 # Should still be 1 because is_live=True on v1

    # 6. Make v2 Live
    wf1.is_live = False
    wf1.save()
    wf2.is_live = True
    wf2.save()

    # Dispatch another event
    event3 = EventIngestionService.ingest_event(event_type="manual", source="test3", payload={})
    dispatcher.dispatch_batch()
    execution3 = Execution.objects.get(event=event3)
    assert execution3.workflow_version == 2

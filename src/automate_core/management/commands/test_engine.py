from django.core.management.base import BaseCommand
from django.utils import timezone
from automate_core.executions.models import Execution, ExecutionStatusChoices
from automate_core.executions.engine import ExecutionEngine
from automate_core.events.models import Event
from automate_core.workflows.models import Automation, Workflow, Trigger

class Command(BaseCommand):
    help = "Test the SRE Execution Engine manually"

    def handle(self, *args, **options):
        # 1. Setup Data
        tenant = "test-tenant-sre"
        auto, _ = Automation.objects.get_or_create(
            tenant_id=tenant, slug="sre-test-auto", defaults={"name": "SRE Test"}
        )
        wf, _ = Workflow.objects.get_or_create(
            automation=auto, version=1, 
            defaults={"graph": {"nodes": [{"id": "step1", "type": "log"}]}}
        )
        trigger, _ = Trigger.objects.get_or_create(
            automation=auto, is_active=True, type="manual", event_type="manual.test"
        )
        event = Event.objects.create(
            tenant_id=tenant, 
            event_type="manual.test", 
            source="cli", 
            payload={},
            occurred_at=timezone.now()
        )
        
        # 2. Create Execution
        execution = Execution.objects.create(
            tenant_id=tenant,
            event=event, 
            automation=auto,
            trigger=trigger,
            workflow_version=1,
            status=ExecutionStatusChoices.QUEUED
        )
        
        self.stdout.write(f"Created Execution {execution.id} (Status: {execution.status})")
        
        # 3. Simulate Worker
        worker_id = "worker-1"
        engine = ExecutionEngine(worker_id=worker_id)
        
        self.stdout.write(f"Worker {worker_id} attempting to run...")
        engine.run_execution(execution.id)
        
        # 4. Verify Final State
        execution.refresh_from_db()
        self.stdout.write(f"Final Status: {execution.status}")
        self.stdout.write(f"Lease Owner (Should be None): {execution.lease_owner}")
        
        if execution.status == ExecutionStatusChoices.SUCCESS:
            self.stdout.write(self.style.SUCCESS("Engine Verification Passed!"))
        else:
             self.stdout.write(self.style.ERROR("Engine Verification Failed."))
             # Check steps
             for step in execution.steps.all():
                 self.stdout.write(f"Step {step.node_key}: {step.status}")

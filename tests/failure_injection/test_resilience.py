from unittest.mock import MagicMock, patch

import pytest

from automate.models import Automation, Execution, ExecutionStatusChoices, ExecutionStep
from automate.runtime import Runtime


class CrashError(Exception):
    pass


@pytest.mark.django_db
class TestFailureInjection:
    """
    Track B: Tests for system resilience against crashes and retry storms.
    """

    def test_worker_crash_mid_step(self, db):
        """
        Simulate a worker dying in the middle of a step execution.
        The step should remain in RUNNING (or FAILED), and logic should exist to rescue it.
        """
        runtime = Runtime()

        # Mock a connector that crashes the process/thread
        with patch("automate.registry.registry.get_connector") as mock_get:
            mock_connector = MagicMock()
            mock_connector.redact.return_value = {}  # Return valid dict for JSONField
            mock_connector.execute.side_effect = CrashError("Worker Died!")
            mock_get.return_value = MagicMock(return_value=mock_connector)

            # Create Dependencies
            from django.utils import timezone

            from automate.models import Automation, Event

            evt = Event.objects.create(tenant_id="test", event_type="test", source="test", occurred_at=timezone.now())
            auto = Automation.objects.create(tenant_id="test", slug="crash-test", name="Crash Test")

            # Create Execution
            execution = Execution.objects.create(status=ExecutionStatusChoices.RUNNING, event=evt, automation=auto)

            # Step Logic
            # We call the internal _run_step to isolate the crash
            try:
                runtime._run_step(execution, "step_crash", "Crasher", "mock_slug", {})
            except CrashError:
                pass  # Worker process would die here

            # Verify State
            step = ExecutionStep.objects.get(node_key="step_crash")
            assert step.status == ExecutionStatusChoices.FAILED
            assert "Worker Died!" in str(step.error_data)

    def test_retry_storm_control(self, db):
        """
        Verify that retries respect the backoff and max_attempts.
        """
        runtime = Runtime()
        # 1. First Failure
        from django.utils import timezone

        from automate.models import Event

        event = Event.objects.create(
            tenant_id="test-tenant", event_type="test", source="test", occurred_at=timezone.now()
        )
        auto = Automation.objects.create(tenant_id="test-tenant", slug="res-auto-storm", name="Resilience Storm Auto")
        execution = Execution.objects.create(
            tenant_id="test-tenant", event=event, automation=auto, status=ExecutionStatusChoices.RUNNING
        )

        # 1. First Failure
        runtime.run_execution(execution.id)
        execution.refresh_from_db()
        assert execution.status == ExecutionStatusChoices.FAILED  # In our sync runtime, we mark failed + log retry
        assert execution.attempt == 1

        # 2. Second Trigger (Retry 1)
        # Manually reset status to allow "picking up" by worker
        execution.status = ExecutionStatusChoices.QUEUED
        execution.save()

        runtime.run_execution(execution.id)
        execution.refresh_from_db()
        assert execution.attempt == 2

        # 3. Third Trigger (Retry 2 - Last one)
        execution.status = ExecutionStatusChoices.QUEUED
        execution.save()

        runtime.run_execution(execution.id)
        execution.refresh_from_db()
        assert execution.attempt == 3

        # 4. Fourth Trigger (Should Fail permanently)
        execution.status = ExecutionStatusChoices.QUEUED
        execution.save()

        # Mock logging to verify "Max retries reached"
        with patch("automate.runtime.logger") as mock_logger:
            runtime.run_execution(execution.id)
            # Should not increment attempts if checking strictly,
            # Or if it attempts and sees max reached, it fails out.

            execution.refresh_from_db()
            assert "Max retries reached" in execution.error_summary

from unittest import mock

import pytest

from automate.models import Automation, Event, Execution, ExecutionStatusChoices, ExecutionStep
from automate.runtime import Runtime


@pytest.mark.django_db
def test_secrets_redaction_on_persist():
    """
    P0.6: Verify inputs and exceptions are redacted.
    """
    # Setup
    # Setup
    from django.utils import timezone

    event = Event.objects.create(
        tenant_id="test-tenant", event_type="manual", source="test", payload={}, occurred_at=timezone.now()
    )
    auto = Automation.objects.create(name="Leak Test", slug="leak-test")
    execution = Execution.objects.create(
        tenant_id="test-tenant", event=event, automation=auto, status=ExecutionStatusChoices.RUNNING
    )

    runtime = Runtime()

    # Mock Connector
    # We use a mocked connector instance
    # Mock Connector Instance
    mock_instance = mock.MagicMock()
    mock_instance.execute.side_effect = ValueError("Fatal error with KEY=super-secret-123")
    mock_instance.redact.side_effect = lambda x: {k: "***" if k == "token" else v for k, v in x.items()}
    # Mock Connector Class
    mock_cls = mock.MagicMock(return_value=mock_instance)

    # We need to inject this connector into the runtime logic.
    # Runtime._run_step calls `registry.get_connector(connector_slug)`.
    # So we patch `automate.registry.get_connector`.

    with (
        mock.patch("automate.registry.registry.get_connector", return_value=mock_cls),
        mock.patch("django.conf.settings.AUTOMATE_ALLOW_RAW_SECRETS", True, create=True),
    ):
        inputs = {"token": "super-secret-123", "other": "value"}

        import contextlib

        with contextlib.suppress(Exception):
            runtime._run_step(execution, "step_1", "Secret Step", "mock-connector", inputs)

        # Verify Step
        step = ExecutionStep.objects.get(node_key="step_1")

        # 1. Inputs Redacted?
        assert step.input_data["token"] == "***"
        assert step.input_data["other"] == "value"

        # 2. Error Data Redacted?
        # Expect "super-secret-123" NOT to be in error message
        assert "super-secret-123" not in str(step.error_data)

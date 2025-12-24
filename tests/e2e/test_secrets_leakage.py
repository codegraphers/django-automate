import pytest
from unittest import mock
from automate.runtime import Runtime
from automate.models import Execution, ExecutionStep, ExecutionStatusChoices, Automation, Event

@pytest.mark.django_db
def test_secrets_redaction_on_persist():
    """
    P0.6: Verify inputs and exceptions are redacted.
    """
    # Setup
    event = Event.objects.create(event_type="manual", payload={})
    auto = Automation.objects.create(name="Leak Test", slug="leak-test")
    execution = Execution.objects.create(event=event, automation=auto, status=ExecutionStatusChoices.RUNNING)
    
    runtime = Runtime()
    
    # Mock Connector
    # We use a mocked connector instance
    mock_connector = mock.MagicMock()
    mock_connector.execute.side_effect = ValueError("Fatal error with KEY=super-secret-123")
    mock_connector.redact.side_effect = lambda x: {k: "***" if k == "token" else v for k, v in x.items()}
    
    # We need to inject this connector into the runtime logic.
    # Runtime._run_step calls `registry.get_connector(connector_slug)`.
    # So we patch `automate.registry.get_connector`.
    
    with mock.patch("automate.registry.registry.get_connector", return_value=mock_connector), \
         mock.patch("django.conf.settings.AUTOMATE_ALLOW_RAW_SECRETS", True, create=True):
        inputs = {"token": "super-secret-123", "other": "value"}
        
        try:
             runtime._run_step(execution, "step_1", "Secret Step", "mock-connector", inputs)
        except Exception:
             pass # Runtime re-raises or swallows? _run_step re-raises usually.
        
        # Verify Step
        step = ExecutionStep.objects.get(step_id="step_1")
        
        # 1. Inputs Redacted?
        assert step.input_data["token"] == "***"
        assert step.input_data["other"] == "value"
        
        # 2. Error Message Redacted?
        # Expect "super-secret-123" NOT to be in error message
        assert "super-secret-123" not in step.error_message

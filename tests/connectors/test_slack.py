"""
Tests for Slack adapter using the canonical ConnectorAdapter pattern.
"""

from unittest.mock import MagicMock, patch

import pytest

from automate_connectors.adapters.slack import SlackAdapter
from automate_connectors.errors import ConnectorError


@pytest.fixture
def slack_adapter():
    """Create a SlackAdapter instance."""
    return SlackAdapter()


def test_slack_adapter_capabilities(slack_adapter):
    """Adapter should expose its capabilities."""
    caps = slack_adapter.capabilities
    assert caps.supports_rate_limit_headers is True


def test_slack_adapter_action_specs(slack_adapter):
    """Adapter should define send_message action."""
    specs = slack_adapter.action_specs
    assert "send_message" in specs
    assert specs["send_message"].name == "send_message"


def test_slack_validate_config(slack_adapter):
    """Config validation should pass for valid config."""
    result = slack_adapter.validate_config({})
    assert result.ok is True


def test_slack_unknown_action(slack_adapter):
    """Unknown actions should raise ConnectorError."""
    with pytest.raises(ConnectorError) as exc:
        slack_adapter.execute("unknown_action", {}, {})
    assert "Unknown action" in str(exc.value)


def test_slack_missing_token(slack_adapter):
    """Missing token should raise auth error."""
    with pytest.raises(ConnectorError) as exc:
        slack_adapter.execute("send_message", {"channel": "#general"}, {})
    assert "token" in str(exc.value).lower()


@patch("automate_connectors.adapters.slack.requests.post")
def test_slack_send_message_success(mock_post, slack_adapter):
    """Successful message send should return data."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"ok": True, "ts": "123"}
    mock_post.return_value.raise_for_status = MagicMock()

    result = slack_adapter.execute(
        "send_message",
        {"channel": "#general", "message": "Hello!"},
        {"profile": {"encrypted_secrets": {"token": "xoxb-test-token"}}}
    )

    assert result.data["ok"] is True
    mock_post.assert_called_once()


@patch("automate_connectors.adapters.slack.requests.post")
def test_slack_rate_limit(mock_post, slack_adapter):
    """Rate limiting should raise retryable error."""
    mock_post.return_value.status_code = 429
    mock_post.return_value.headers = {"Retry-After": "5"}

    with pytest.raises(ConnectorError) as exc:
        slack_adapter.execute(
            "send_message",
            {"channel": "#general"},
            {"profile": {"encrypted_secrets": {"token": "xoxb-test"}}}
        )

    assert exc.value.retryable is True

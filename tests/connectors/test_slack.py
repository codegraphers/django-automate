import hashlib
import hmac
import time
from unittest.mock import MagicMock

import pytest

from automate_connectors.providers.slack import SlackConnector
from automate_core.providers.base import ProviderContext
from automate_core.providers.errors import AutomateError


@pytest.fixture
def mock_ctx():
    secrets = MagicMock()
    secrets.resolve.side_effect = lambda x: x # return the ref as the value
    return ProviderContext(
        tenant_id="t1",
        correlation_id="c1",
        actor_id="user1",
        purpose="test",
        secrets=secrets,
        policy=None,
        logger=None,
        now=lambda: None
    )

def test_slack_action(mock_ctx):
    config = {
        "bot_token": {"ref": "xoxb-valid"},
        "signing_secret": {"ref": "secret"}
    }
    connector = SlackConnector(config, ctx=mock_ctx)

    # Test execute
    res = connector.execute_action("post_message", {"channel": "#general", "text": "Hello"})
    assert res["ok"] is True

    # Test Auth Failure
    config_bad = {
        "bot_token": {"ref": "invalid"},
        "signing_secret": {"ref": "secret"}
    }
    connector_bad = SlackConnector(config_bad, ctx=mock_ctx)
    with pytest.raises(AutomateError) as exc:
        connector_bad.execute_action("post_message", {"text": "hi"})
    assert str(exc.value.code) == "unauthorized"

def test_slack_webhook_verify(mock_ctx):
    signing_secret = "my-secret"
    config = {
        "bot_token": {"ref": "xoxb"},
        "signing_secret": {"ref": signing_secret}
    }
    connector = SlackConnector(config, ctx=mock_ctx)

    req_body = b"foo=bar"
    ts = str(int(time.time()))
    basename = f"v0:{ts}:{req_body.decode('utf-8')}"

    sig = "v0=" + hmac.new(
        signing_secret.encode('utf-8'),
        basename.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": sig
    }

    assert connector.verify_webhook(headers, req_body) is True

    # Tamper
    assert connector.verify_webhook(headers, b"foo=baz") is False

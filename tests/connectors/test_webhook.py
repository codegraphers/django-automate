import hashlib
import hmac
from unittest.mock import MagicMock

import pytest

from automate_connectors.providers.webhook import WebhookConnector
from automate_core.providers.base import ProviderContext


@pytest.fixture
def mock_ctx():
    return ProviderContext(
        tenant_id="t1", correlation_id="c1", actor_id="user", purpose="test",
        secrets=MagicMock(resolve=lambda x: x), policy=None, logger=None, now=lambda: None
    )

def test_webhook_send(mock_ctx):
    conn = WebhookConnector({}, ctx=mock_ctx)
    res = conn.execute_action("send", {"url": "http://example.com"})
    assert res["status"] == 200

def test_webhook_verify_hmac(mock_ctx):
    secret = "xyz"
    conn = WebhookConnector({
        "signing_secret": {"ref": secret},
        "verification_method": "hmac_sha256"
    }, ctx=mock_ctx)

    body = b"hello"
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    # Valid
    assert conn.verify_webhook({"X-Signature": sig}, body) is True
    # Valid with prefix
    assert conn.verify_webhook({"X-Hub-Signature-256": f"sha256={sig}"}, body) is True

    # Invalid
    assert conn.verify_webhook({"X-Signature": "bad"}, body) is False

def test_webhook_verify_none(mock_ctx):
    conn = WebhookConnector({"verification_method": "none"}, ctx=mock_ctx)
    assert conn.verify_webhook({}, b"any") is True

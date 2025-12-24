from unittest.mock import MagicMock, patch

import pytest

from automate.models import ConnectionProfile
from automate_connectors.adapters.slack import SlackAdapter as SlackConnector


@pytest.mark.django_db
def test_secrets_resolution_in_connector():
    """
    P0.5: Verify SlackConnector resolves secrets via backend.
    """
    # 1. Setup Profile
    profile = ConnectionProfile.objects.create(
        name="Test Slack",
        slug="test-slack",
        connector_slug="slack",
        encrypted_secrets={"token": "env://SLACK_TEST_TOKEN"},
        enabled=True
    )

    connector = SlackConnector()

    # 2. Mock Env & Requests
    with patch.dict("os.environ", {"SLACK_TEST_TOKEN": "xoxb-real-token"}), patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "ts": "123"}
        mock_post.return_value = mock_response

        # Execute
        connector.execute("send_message", {"channel": "C123"}, {
            "profile": {"encrypted_secrets": {"token": "xoxb-real-token"}}
        })

        # Verify Header
        args, kwargs = mock_post.call_args
        headers = kwargs.get("headers", {})
        assert headers["Authorization"] == "Bearer xoxb-real-token"


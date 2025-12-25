from unittest.mock import MagicMock, patch

import pytest

from automate_core.providers.base import ProviderContext
from automate_core.providers.schemas.base import SecretRef
from automate_core.providers.schemas.llm import ChatMessage, ChatRequest
from automate_llm.providers.openai_chat import OpenAIConfig, OpenAIProvider


@pytest.fixture
def mock_ctx():
    secrets = MagicMock()
    secrets.resolve.return_value = "sk-test-key-resolved"
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

@pytest.fixture
def provider(mock_ctx):
    config = {
        "api_key": {"ref": "env:OPENAI_API_KEY"},
        "default_model": "gpt-4-test"
    }
    with patch("automate_llm.providers.openai_chat.openai") as mock_openai:
        p = OpenAIProvider(config, ctx=mock_ctx)
        p.client = MagicMock() # Mock the client instance created in __init__
        return p

def test_openai_init(mock_ctx):
    config = {"api_key": {"ref": "env:KEY"}}
    with patch("automate_llm.providers.openai_chat.openai") as mock_pkg:
        p = OpenAIProvider(config, ctx=mock_ctx)
        # Check secret resolution
        mock_ctx.secrets.resolve.assert_called_with("env:KEY")
        # Check client init
        mock_pkg.OpenAI.assert_called()

def test_chat_call(provider):
    # Mock response
    mock_choice = MagicMock()
    mock_choice.message.content = "Hello world"
    mock_choice.finish_reason = "stop"

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.model = "gpt-4-test"
    mock_resp.usage.prompt_tokens = 10
    mock_resp.usage.completion_tokens = 2
    mock_resp.usage.total_tokens = 12

    provider.client.chat.completions.create.return_value = mock_resp

    req = ChatRequest(messages=[ChatMessage(role="user", content="Hi")])
    resp = provider.chat(req)

    assert resp.content == "Hello world"
    assert resp.usage["total_tokens"] == 12

    # Verify call args
    call_kwargs = provider.client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4-test"
    assert call_kwargs["messages"][0]["content"] == "Hi"

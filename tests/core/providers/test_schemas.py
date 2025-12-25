import pytest
from pydantic import ValidationError

from automate_core.providers.schemas.base import SecretRef
from automate_core.providers.schemas.llm import ChatMessage, ChatRequest


def test_secret_ref():
    s = SecretRef(ref="env:MY_KEY")
    assert s.ref == "env:MY_KEY"

    # Validation error if missing ref
    with pytest.raises(ValidationError):
        SecretRef()

def test_chat_request_valid():
    req = ChatRequest(
        messages=[
            ChatMessage(role="system", content="You are a bot."),
            ChatMessage(role="user", content="Hello!")
        ],
        model="gpt-4",
        temperature=0.5
    )
    assert req.model == "gpt-4"
    assert len(req.messages) == 2
    assert req.messages[0].role == "system"

def test_chat_request_defaults():
    req = ChatRequest(
        messages=[ChatMessage(role="user", content="Hi")]
    )
    assert req.temperature == 0.7
    assert req.stream is False

def test_chat_request_invalid_role():
    with pytest.raises(ValidationError):
        ChatMessage(role="admin", content="Invalid role") # 'admin' not in Literal

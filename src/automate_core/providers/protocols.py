from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from .schemas.llm import ChatRequest, ChatResponse, ChatStreamEvent


@runtime_checkable
class ChatLLMProvider(Protocol):
    """Protocol for providers that support Chat interactions."""

    def chat(self, req: ChatRequest) -> ChatResponse:
        """Synchronous chat completion."""
        ...

    def chat_stream(self, req: ChatRequest) -> Iterable[ChatStreamEvent]:
        """Streaming chat completion."""
        ...

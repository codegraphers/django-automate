from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ..errors import LLMError
from ..types import ChatRequest, ChatResponse, CostEstimate


class ProviderAdapter(ABC):
    """
    Provider adapters must:
      - be stateless or cheaply-instantiable
      - never contain policy logic
      - normalize exceptions into LLMError
    """
    code: str  # e.g. "openai"

    def __init__(self, *, base_url: str | None = None, headers: dict[str, str] | None = None) -> None:
        self.base_url = base_url
        self.headers = headers or {}

    @abstractmethod
    def chat(self, req: ChatRequest, *, api_key: str) -> ChatResponse:
        raise NotImplementedError

    def stream(self, req: ChatRequest, *, api_key: str) -> Iterator[ChatResponse]:
        raise NotImplementedError("Streaming not implemented for this adapter")

    @abstractmethod
    def estimate_cost(self, req: ChatRequest) -> CostEstimate:
        raise NotImplementedError

    @property
    def capabilities(self) -> dict[str, bool]:
        """Feature flags: supports_streaming, supports_tools, etc."""
        return {}

    @abstractmethod
    def normalize_error(self, exc: Exception) -> LLMError:
        raise NotImplementedError

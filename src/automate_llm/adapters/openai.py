from __future__ import annotations
from typing import Any

from .base import ProviderAdapter
from ..types import ChatRequest, ChatResponse, Usage, CostEstimate
from ..errors import LLMError, LLMErrorCode

class OpenAIAdapter(ProviderAdapter):
    code = "openai"

    def chat(self, req: ChatRequest, *, api_key: str) -> ChatResponse:
        # Stub implementation as originally provided in the skeleton
        # In a real implementation, this would use `openai` library
        raise NotImplementedError("OpenAI Chat Not Implemented")

    def estimate_cost(self, req: ChatRequest) -> CostEstimate:
        # TODO: implement model pricing lookup via configured table
        return CostEstimate(estimated_cost=0.0)

    def normalize_error(self, exc: Exception) -> LLMError:
        # TODO: map provider exceptions/status codes to normalized codes
        return LLMError(code=LLMErrorCode.INTERNAL_ERROR, message_safe=str(exc), retryable=False, provider=self.code)

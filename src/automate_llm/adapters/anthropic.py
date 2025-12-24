from __future__ import annotations

import logging

from ..errors import LLMError, LLMErrorCode
from ..pricing import ModelPricing
from ..types import ChatRequest, ChatResponse, CostEstimate, ToolCall, Usage
from .base import ProviderAdapter

logger = logging.getLogger(__name__)

class AnthropicAdapter(ProviderAdapter):
    code = "anthropic"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "supports_streaming": False, # Todo
            "supports_tools": True,
            "supports_vision": True
        }

    def chat(self, req: ChatRequest, *, api_key: str) -> ChatResponse:
        try:
            import anthropic
        except ImportError:
            raise LLMError(LLMErrorCode.INTERNAL_ERROR, "anthropic package not installed")

        client = anthropic.Anthropic(api_key=api_key)

        # Convert messages
        system_prompt = None
        messages = []
        for m in req.messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                messages.append({"role": m.role, "content": m.content})

        params = {
            "model": req.model,
            "messages": messages,
            "max_tokens": req.max_tokens or 1024,
            "temperature": req.temperature,
        }
        if system_prompt:
            params["system"] = system_prompt

        # Tools
        if req.tools:
            params["tools"] = [t.to_dict() for t in req.tools]

        try:
            resp = client.messages.create(**params)

            content_text = ""
            tool_calls = []

            for block in resp.content:
                if block.type == "text":
                    content_text += block.text
                elif block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input # Anthropic returns dict natively
                    ))

            return ChatResponse(
                content=content_text,
                role=resp.role,
                tool_calls=tuple(tool_calls) if tool_calls else (),
                usage=Usage(
                    input_tokens=resp.usage.input_tokens,
                    output_tokens=resp.usage.output_tokens
                ),
                provider_info={"id": resp.id, "model": resp.model}
            )

        except Exception as e:
            raise self.normalize_error(e)

    def estimate_cost(self, req: ChatRequest) -> CostEstimate:
        # Simple stub estimation
        pricing = ModelPricing.get(req.model)
        # Rough token count estimate (chars / 4)
        input_chars = sum(len(m.content) for m in req.messages)
        input_tokens = int(input_chars / 3.5)

        cost = (input_tokens / 1000) * pricing.input_price_per_1k
        # Output unknown, assume max? or 0 for base cost
        return CostEstimate(total_cost_usd=cost, currency="USD", details={"input_estimate": input_tokens})

    def normalize_error(self, exc: Exception) -> LLMError:
        import anthropic
        if isinstance(exc, anthropic.AuthenticationError):
             return LLMError(LLMErrorCode.AUTH_FAILED, str(exc), retryable=False)
        if isinstance(exc, anthropic.RateLimitError):
             return LLMError(LLMErrorCode.RATE_LIMITED, str(exc), retryable=True)
        if isinstance(exc, anthropic.APIStatusError):
             return LLMError(LLMErrorCode.PROVIDER_ERROR, str(exc), retryable=exc.status_code >= 500)
        return LLMError(LLMErrorCode.INTERNAL_ERROR, f"Anthropic Error: {exc}", retryable=False)

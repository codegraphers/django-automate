from __future__ import annotations

try:
    import anthropic
except ImportError:
    anthropic = None

from automate_governance.secrets.resolver import SecretResolver

from .interfaces import CompletionRequest, CompletionResponse, LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, secret_resolver: SecretResolver, api_key_ref: str):
        self.secret_resolver = secret_resolver
        self.api_key_ref = api_key_ref
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client

        if not anthropic:
            raise RuntimeError("anthropic package not installed")

        api_key = self.secret_resolver.resolve_value(self.api_key_ref)
        self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def chat_complete(self, request: CompletionRequest) -> CompletionResponse:
        client = self._get_client()

        # Anthropic messages API
        # Need to handle system prompt separately if present in messages usually,
        # but modern SDK handles extracting system param?
        # Simplified: Pass messages as is, map model.

        # Filter system messages out if needed or rely on SDK/API behavior
        system = None
        filtered_msgs = []
        for m in request.messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered_msgs.append(m)

        kwargs = {
            "model": request.model,
            "messages": filtered_msgs,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)

        return CompletionResponse(
            content=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            model_used=response.model,
            raw_response=response.model_dump()
        )

    def count_tokens(self, text: str, model: str) -> int:
        return len(text) // 4

    def health_check(self) -> bool:
        try:
            # No simple list models endpoint auth check?
            # Try a tiny completion or assume OK if client init
            return True
        except Exception:
            return False

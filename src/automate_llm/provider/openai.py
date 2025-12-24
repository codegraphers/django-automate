from __future__ import annotations

# Using requests for zero-dependency implementation relative to SDK version churn,
# or better yet, assume `openai` package is present as per pyproject.toml deps (though not strictly enforced yet).
# For robustness in this plan, I'll use direct HTTP or check imports.
# The plan mentions "Integration with openai SDK".

try:
    import openai
except ImportError:
    openai = None

from automate_governance.secrets.resolver import SecretResolver
from automate_llm.registry import register_provider

from .interfaces import CompletionRequest, CompletionResponse, LLMProvider


@register_provider("openai")
@register_provider("open-ai")  # Also register hyphenated version
class OpenAIProvider(LLMProvider):
    def __init__(self, secret_resolver: SecretResolver, api_key_ref: str, org_id_ref: str | None = None):
        self.secret_resolver = secret_resolver
        self.api_key_ref = api_key_ref
        self.org_id_ref = org_id_ref
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client

        if not openai:
            raise RuntimeError("openai package not installed")

        api_key = self.secret_resolver.resolve_value(self.api_key_ref)
        org_id = self.secret_resolver.resolve_value(self.org_id_ref) if self.org_id_ref else None

        self._client = openai.Client(api_key=api_key, organization=org_id)
        return self._client

    def chat_complete(self, request: CompletionRequest) -> CompletionResponse:
        client = self._get_client()

        # Mapping generic request to OpenAI params
        params = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stop": request.stop,
            "stream": False,  # Streaming not supported in this simplified interface yet
        }

        response = client.chat.completions.create(**params)
        choice = response.choices[0]

        return CompletionResponse(
            content=choice.message.content or "",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            model_used=response.model,
            raw_response=response.model_dump(),
        )

    def count_tokens(self, text: str, model: str) -> int:
        # Stub: usually requires tiktoken.
        # Approx: 4 chars / token
        return len(text) // 4

    def health_check(self) -> bool:
        try:
            self._get_client().models.list()
            return True
        except Exception:
            return False

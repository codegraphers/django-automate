from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

try:
    import openai
except ImportError:
    openai = None # Handled in validation

from automate_core.providers.base import BaseProvider, CapabilitySpec, ProviderContext
from automate_core.providers.errors import AutomateError, ErrorCodes, requests_exception_to_automate_error
from automate_core.providers.schemas.base import SecretRef
from automate_core.providers.schemas.llm import ChatRequest, ChatResponse, ChatStreamEvent


class OpenAIConfig(BaseModel):
    api_key: SecretRef
    base_url: str | None = "https://api.openai.com/v1"
    organization: str | None = None
    default_model: str = "gpt-4o"
    timeout_s: float = 60.0
    max_retries: int = 2

class OpenAIProvider(BaseProvider):
    key = "openai"
    display_name = "OpenAI"

    @classmethod
    def capabilities(cls) -> list[CapabilitySpec]:
        return [
            CapabilitySpec(name="llm.chat", modalities={"text"}, streaming=True),
            # CapabilitySpec(name="llm.embeddings", modalities={"text"}, streaming=False),
        ]

    @classmethod
    def config_schema(cls) -> type[BaseModel]:
        return OpenAIConfig

    def __init__(self, config: dict[str, Any], *, ctx: ProviderContext):
        if openai is None:
            raise ImportError("OpenAI python package is not installed.")

        self.ctx = ctx
        self.cfg = OpenAIConfig(**config)

        # Resolve secrets using context
        # Assumes ctx.secrets has resolve method or it's just available.
        # Design said "ctx.secrets" is a SecretResolver protocol.
        api_key = self.cfg.api_key.ref
        if hasattr(self.ctx.secrets, 'resolve'):
             api_key = self.ctx.secrets.resolve(api_key)
        elif self.cfg.api_key.ref.startswith("sk-"): # Allow direct raw key for dev/testing if not resolved
             api_key = self.cfg.api_key.ref

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=self.cfg.base_url,
            organization=self.cfg.organization,
            timeout=self.cfg.timeout_s,
            max_retries=self.cfg.max_retries
        )

    def normalize_error(self, exc: Exception) -> Exception:
        if isinstance(exc, openai.APIStatusError):
            return requests_exception_to_automate_error(exc, provider=self.key)
        if isinstance(exc, openai.APITimeoutError):
            return AutomateError(ErrorCodes.TIMEOUT, "Request timed out", True, provider=self.key, original_exception=exc)
        if isinstance(exc, openai.APIConnectionError):
            return AutomateError(ErrorCodes.PROVIDER_UNAVAILABLE, "Connection failed", True, provider=self.key, original_exception=exc)

        return AutomateError(ErrorCodes.INTERNAL, str(exc), provider=self.key, original_exception=exc)

    def chat(self, req: ChatRequest) -> ChatResponse:
        try:
            msgs = [{"role": m.role, "content": m.content} for m in req.messages]

            # Map parameters
            params = {
                "model": req.model or self.cfg.default_model,
                "messages": msgs,
                "temperature": req.temperature,
                "stream": False,
            }
            if req.max_output_tokens:
                params["max_tokens"] = req.max_output_tokens
            if req.response_format:
                params["response_format"] = req.response_format
            if req.stop:
                params["stop"] = req.stop
            # Tools not implemented yet in v1 minimal

            response = self.client.chat.completions.create(**params)

            choice = response.choices[0]

            return ChatResponse(
                content=choice.message.content,
                finish_reason=choice.finish_reason,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            )

        except Exception as e:
            raise self.normalize_error(e) from e

    def chat_stream(self, req: ChatRequest) -> Iterable[ChatStreamEvent]:
        try:
            msgs = [{"role": m.role, "content": m.content} for m in req.messages]

            params = {
                "model": req.model or self.cfg.default_model,
                "messages": msgs,
                "temperature": req.temperature,
                "stream": True,
            }
            if req.max_output_tokens:
                params["max_tokens"] = req.max_output_tokens

            stream = self.client.chat.completions.create(**params)

            for chunk in stream:
                delta = chunk.choices[0].delta
                content = delta.content or ""
                finish = chunk.choices[0].finish_reason

                yield ChatStreamEvent(
                    content_delta=content,
                    finish_reason=finish
                )

        except Exception as e:
            raise self.normalize_error(e) from e

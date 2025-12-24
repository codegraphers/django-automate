import logging
from collections.abc import Iterable
from typing import Any

from automate_modal.contracts import Capability, ExecutionCtx, ModalResult, ModalTaskType, StreamEvent
from automate_modal.registry import ProviderBase

# Import from automate_llm without hard dependency
try:
    from automate_llm.provider.interfaces import CompletionRequest
    from automate_llm.registry import get_provider_class
except ImportError:
    get_provider_class = None

logger = logging.getLogger(__name__)


class SecretResolverAdapter:
    """Adapts automate_modal.contracts.SecretsResolver to automate_governance.SecretResolver."""

    def __init__(self, modal_resolver):
        self._resolver = modal_resolver

    def resolve_value(self, secret_ref: str) -> str:
        if not secret_ref:
            return ""
        return self._resolver.resolve(secret_ref)


class LLMBridgeCapability(Capability):
    def __init__(self, task_type: str, provider_instance: "LLMBridgeProvider"):
        self.task_type = task_type
        self.parent = provider_instance

    def validate(self, req: dict[str, Any]) -> None:
        if "messages" not in req:
            raise ValueError("LLM request must contain 'messages'")

    def _get_provider_instance(self, ctx: ExecutionCtx):
        config = self.parent.config or {}
        provider_slug = config.get("upstream_provider")

        if not provider_slug:
            raise ValueError("Bridge configuration missing 'upstream_provider'")

        if not get_provider_class:
            raise RuntimeError("automate_llm package not found")

        provider_cls = get_provider_class(provider_slug)
        if not provider_cls:
            raise ValueError(f"LLM Provider '{provider_slug}' not found in automate_llm registry")

        resolver = SecretResolverAdapter(ctx.secrets)

        try:
            api_key_ref = config.get("api_key_ref", config.get("api_key"))
            org_id_ref = config.get("org_id_ref", config.get("org_id"))

            return ProviderCls(secret_resolver=resolver, api_key_ref=api_key_ref, org_id_ref=org_id_ref)
        except TypeError:
            # Fallback
            return ProviderCls(config=config, secret_resolver=resolver)

    def run(self, req: dict[str, Any], ctx: ExecutionCtx) -> ModalResult:
        provider = self._get_provider_instance(ctx)

        request = CompletionRequest(
            model=req.get("model", "gpt-4"),
            messages=req.get("messages", []),
            temperature=req.get("temperature", 0.7),
            max_tokens=req.get("max_tokens", 1000),
            stop=req.get("stop"),
            stream=False,
        )

        response = provider.chat_complete(request)

        return ModalResult(
            task_type=self.task_type,
            outputs={"content": response.content},
            usage=response.usage,
            raw_provider_meta=response.raw_response,
        )

    def stream(self, req: dict[str, Any], ctx: ExecutionCtx) -> Iterable[StreamEvent]:
        raise NotImplementedError("Streaming not supported for bridged LLM providers yet")


class LLMBridgeProvider(ProviderBase):
    """
    Bridges automate_modal to automate_llm's providers.
    """

    key = "llm-bridge"
    display_name = "Legacy LLM Bridge"
    config = {}

    @classmethod
    def config_schema(cls) -> dict:
        return {
            "type": "object",
            "required": ["upstream_provider", "api_key_ref"],
            "properties": {
                "upstream_provider": {"type": "string", "enum": ["openai", "anthropic"]},
                "api_key_ref": {"type": "string"},
                "org_id_ref": {"type": "string"},
            },
        }

    @property
    def capabilities(self) -> list[Capability]:
        return [LLMBridgeCapability(ModalTaskType.LLM_CHAT, self)]

    def build_client(self, cfg: dict, ctx: ExecutionCtx) -> Any:
        pass

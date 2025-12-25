
from pydantic import BaseModel

from automate_core.providers.base import BaseProvider, CapabilitySpec, ProviderContext
from automate_core.providers.errors import AutomateError, ErrorCodes
from automate_core.providers.schemas.llm import ChatRequest, ChatResponse


class MyProviderConfig(BaseModel):
    api_key: str

class MyProvider(BaseProvider):
    key = "my_provider"
    display_name = "My Example Provider"

    @classmethod
    def capabilities(cls) -> list[CapabilitySpec]:
        return [
            CapabilitySpec(name="llm.chat", modalities={"text"}, streaming=False)
        ]

    @classmethod
    def config_schema(cls) -> type[BaseModel]:
        return MyProviderConfig

    def __init__(self, config: dict, *, ctx: ProviderContext):
        self.config = MyProviderConfig(**config)
        self.ctx = ctx

    def normalize_error(self, exc: Exception) -> Exception:
        return AutomateError(ErrorCodes.INTERNAL, str(exc), original_exception=exc)

    def chat(self, req: ChatRequest) -> ChatResponse:
        return ChatResponse(
            content="Hello from MyProvider!",
            model=req.model or "default",
            usage={"total_tokens": 10}
        )

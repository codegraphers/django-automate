from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    # Forward refs for context
    class SecretResolver(Protocol):
        def resolve(self, secret_ref: str) -> str: ...
    class PolicyEvaluator(Protocol):
        def check(self, action: str, resource: Any) -> bool: ...
    class StructuredLogger(Protocol):
        def info(self, msg: str, **kwargs): ...
        def error(self, msg: str, **kwargs): ...
        def warn(self, msg: str, **kwargs): ...

@dataclass(frozen=True)
class ProviderContext:
    tenant_id: str
    correlation_id: str
    actor_id: str | None
    purpose: str  # "endpoint.run", "workflow.step", etc.

    # We use 'Any' here to avoid circular dependencies for now,
    # but the Protocol definitions above clarify intent.
    secrets: Any
    policy: Any
    logger: Any
    now: Callable[[], datetime]

@dataclass(frozen=True)
class CapabilitySpec:
    name: str                     # e.g., "llm.chat"
    modalities: set[str]          # {"text", "image"}
    streaming: bool               # supports streaming?
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    formats: dict[str, list[str]] | None = None # e.g. {"audio": ["mp3"]}

class BaseProvider(ABC):
    key: str
    display_name: str

    @classmethod
    @abstractmethod
    def capabilities(cls) -> list[CapabilitySpec]:
        """Return the capabilities this provider supports."""
        ...

    @classmethod
    @abstractmethod
    def config_schema(cls) -> type[BaseModel]:
        """Return the Pydantic schema for configuration."""
        ...

    @abstractmethod
    def __init__(self, config: dict[str, Any], *, ctx: ProviderContext):
        """Initialize the provider with config and context."""
        ...

    @abstractmethod
    def normalize_error(self, exc: Exception) -> "Exception":
        """Convert a provider-specific error into a canonical AutomateError."""
        # Note: We return Exception here to avoid circular import with failures module
        # ideally this returns AutomateError.
        ...

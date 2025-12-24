"""
Provider and Registry Base Classes
"""
from abc import ABC, abstractmethod
from typing import Any

from .contracts import Capability, ExecutionCtx


class ProviderBase(ABC):
    """Base class for all Multi-Modal Providers."""
    key: str
    display_name: str

    @property
    @abstractmethod
    def capabilities(self) -> list[Capability]:
        """Return list of capability instances."""
        pass

    def configure(self, config: dict):
        """Receive configuration at runtime."""
        self.config = config

    @classmethod
    @abstractmethod
    def config_schema(cls) -> dict:
        """JSON schema for admin + settings validation."""
        pass

    @classmethod
    def supported_tasks(cls) -> list[str]:
        """List of task types this provider supports."""
        # Note: This requires instantiation if capabilities are dynamic,
        # but for static providers we can inspect the class if needed.
        # For now, we assume this is called on an instance or we instantiate to check.
        return []

    @abstractmethod
    def build_client(self, cfg: dict, ctx: ExecutionCtx) -> Any:
        """Initialize SDK client using SecretRef through ctx.secrets."""
        pass


class ProviderRegistry:
    """Registry for discovering and retrieving providers."""

    _providers: dict[str, type[ProviderBase]] = {}

    @classmethod
    def register(cls, provider_cls: type[ProviderBase]) -> None:
        cls._providers[provider_cls.key] = provider_cls

    @classmethod
    def get(cls, key: str) -> type[ProviderBase]:
        if key not in cls._providers:
            raise KeyError(f"Provider '{key}' not registered.")
        return cls._providers[key]

    @classmethod
    def all(cls) -> dict[str, type[ProviderBase]]:
        return dict(cls._providers)

# Global registry instance if needed, or just use class methods
registry = ProviderRegistry()

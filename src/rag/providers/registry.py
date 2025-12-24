"""
RAG Provider Registry

Central registry for retrieval providers.
Providers register themselves on app startup.
"""
import logging

from .base import RetrievalProvider

logger = logging.getLogger(__name__)

# Global registry
_providers: dict[str, RetrievalProvider] = {}


def register_provider(provider: RetrievalProvider) -> None:
    """Register a retrieval provider."""
    if provider.key in _providers:
        logger.warning(f"Overwriting provider: {provider.key}")
    _providers[provider.key] = provider
    logger.info(f"Registered RAG provider: {provider.key}")


def unregister_provider(key: str) -> None:
    """Unregister a provider by key."""
    if key in _providers:
        del _providers[key]


def get_retrieval_provider(key: str) -> RetrievalProvider:
    """Get a registered provider by key."""
    if key not in _providers:
        raise ValueError(f"Unknown retrieval provider: {key}. Available: {list(_providers.keys())}")
    return _providers[key]


def list_providers() -> dict[str, RetrievalProvider]:
    """List all registered providers."""
    return dict(_providers)


def autodiscover() -> None:
    """
    Auto-discover and register built-in providers.
    Called from RagConfig.ready()
    """
    # Import built-in providers to trigger registration
    from . import external, local

    # Register providers
    register_provider(external.ExternalRetrievalProvider())
    register_provider(local.LocalRetrievalProvider())

    logger.info(f"RAG provider autodiscovery complete. Registered: {list(_providers.keys())}")

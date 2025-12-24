"""
LLM Provider Registry

Maps provider slugs to their implementation classes.
This allows runtime to dynamically instantiate providers without hardcoding.
"""
from typing import Dict, Type, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .provider.interfaces import LLMProvider

# --- Provider Registry ---
_PROVIDER_REGISTRY: Dict[str, Type["LLMProvider"]] = {}

def register_provider(slug: str):
    """Decorator to register a provider class."""
    def decorator(cls):
        _PROVIDER_REGISTRY[slug] = cls
        return cls
    return decorator

def get_provider_class(slug: str) -> Type["LLMProvider"] | None:
    """Get a provider class by slug. Returns None if not found."""
    # Lazy import built-in providers on first access
    if not _PROVIDER_REGISTRY:
        try:
            import automate_llm.provider.openai  # noqa - triggers registration
            import automate_llm.provider.anthropic  # noqa
        except ImportError as e:
            pass
    return _PROVIDER_REGISTRY.get(slug)

def list_registered_providers() -> list[str]:
    """List all registered provider slugs."""
    return list(_PROVIDER_REGISTRY.keys())

# --- Template Renderer Registry (used by PromptCompiler) ---
_RENDERER_REGISTRY: Dict[str, Type[Any]] = {}

def register_renderer(template_type: str):
    """Decorator to register a renderer class."""
    def decorator(cls):
        _RENDERER_REGISTRY[template_type] = cls
        return cls
    return decorator

def get_renderer_cls(template_type: str) -> Type[Any]:
    """Get renderer class for a template type."""
    if template_type not in _RENDERER_REGISTRY:
        # Fallback to a simple passthrough renderer
        class PassthroughRenderer:
            def render(self, template, inputs):
                if isinstance(template, str):
                    return template.format(**inputs)
                return template
        return PassthroughRenderer
    return _RENDERER_REGISTRY[template_type]

# Note: Delayed import of providers to avoid circular dependency issues
# Providers will self-register when their modules are imported elsewhere

# --- Adapter Registry (used by RunExecutor) ---
_ADAPTER_REGISTRY: Dict[str, Type[Any]] = {}

def register_adapter(provider_slug: str):
    """Decorator to register an adapter class for a provider."""
    def decorator(cls):
        _ADAPTER_REGISTRY[provider_slug] = cls
        return cls
    return decorator

def get_adapter_cls(provider_slug: str) -> Type[Any] | None:
    """Get adapter class for a provider. Returns None if not found."""
    return _ADAPTER_REGISTRY.get(provider_slug)

# --- Plugin Loading (called from apps.ready()) ---
def load_entrypoint_plugins():
    """Load plugins via setuptools entry_points. No-op stub for now."""
    # TODO: Implement proper entry_point discovery for extensibility
    pass




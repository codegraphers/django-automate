try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata  # type: ignore

import builtins
from dataclasses import dataclass
from typing import Any, Optional

from django.conf import settings
from django.utils.module_loading import import_string

from .base import BaseProvider, CapabilitySpec


@dataclass
class ProviderDescriptor:
    key: str
    cls: type[BaseProvider]
    capabilities: list[CapabilitySpec]
    version: str = "0.0.0"

class ProviderRegistry:
    _instance: Optional["ProviderRegistry"] = None

    def __init__(self):
        self._providers: dict[str, ProviderDescriptor] = {}
        self._capabilities_index: dict[str, list[str]] = {} # cap_name -> list[provider_key]
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self, force_reload: bool = False):
        if self._loaded and not force_reload:
            return

        self._providers.clear()
        self._capabilities_index.clear()

        # 1. Load from Entrypoints (Third-party)
        self._load_from_entrypoints()

        # 2. Load from Settings (Overrides / Internal)
        self._load_from_settings()

        self._loaded = True

    def _load_from_entrypoints(self):
        # Using importlib.metadata to find entry points group 'django_automate.providers'
        # Note: behavior varies slightly by python version, handling 3.10+ style
        try:
            entry_points = importlib_metadata.entry_points()
            # 3.10+ returns SelectableGroups, older dict
            if hasattr(entry_points, 'select'):
                eps = entry_points.select(group='django_automate.providers')
            else:
                eps = entry_points.get('django_automate.providers', [])

            for ep in eps:
                try:
                    cls = ep.load()
                    self._register_class(cls)
                except Exception as e:
                    # Log warning but don't crash
                    print(f"Warning: Failed to load provider entrypoint {ep.name}: {e}")
        except Exception as e:
             print(f"Warning: Error scanning entrypoints: {e}")

    def _load_from_settings(self):
        providers_list = getattr(settings, "AUTOMATE_PROVIDERS", [])
        for path in providers_list:
            try:
                cls = import_string(path)
                self._register_class(cls)
            except Exception as e:
                print(f"Warning: Failed to load provider from settings {path}: {e}")

    def _register_class(self, cls: Any):
        if not issubclass(cls, BaseProvider):
            print(f"Warning: {cls} is not a subclass of BaseProvider. Skipping.")
            return

        # Instantiate (or just inspect class methods)
        # We assume capabilities() is a class method as per interface
        try:
            key = cls.key
            caps = cls.capabilities()

            desc = ProviderDescriptor(
                key=key,
                cls=cls,
                capabilities=caps
            )

            # Register
            self._providers[key] = desc

            # Index capabilities
            for cap in caps:
                if cap.name not in self._capabilities_index:
                    self._capabilities_index[cap.name] = []
                self._capabilities_index[cap.name].append(key)

        except Exception as e:
            print(f"Warning: Failed to inspect provider class {cls}: {e}")

    def list(self) -> list[ProviderDescriptor]:
        if not self._loaded: self.load()
        return list(self._providers.values())

    def get(self, key: str) -> ProviderDescriptor | None:
        if not self._loaded: self.load()
        return self._providers.get(key)

    def resolve_for(self, capability: str) -> builtins.list[ProviderDescriptor]:
        if not self._loaded: self.load()
        keys = self._capabilities_index.get(capability, [])
        return [self._providers[k] for k in keys if k in self._providers]

# Convenience global
def registry() -> ProviderRegistry:
    return ProviderRegistry.get_instance()

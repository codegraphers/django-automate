from __future__ import annotations
from typing import Type, Dict
from .adapters.base import ConnectorAdapter

class ConnectorRegistry:
    def __init__(self):
        self._connectors: Dict[str, Type[ConnectorAdapter]] = {}

    def register(self, adapter_cls: Type[ConnectorAdapter]):
        """Register a connector adapter class."""
        self._connectors[adapter_cls.code] = adapter_cls

    def get_adapter_cls(self, code: str) -> Type[ConnectorAdapter]:
        if code not in self._connectors:
            raise ValueError(f"Connector '{code}' not found")
        return self._connectors[code]

# Global Singleton
_registry = ConnectorRegistry()

def get_connector_registry() -> ConnectorRegistry:
    return _registry

def register_connector(cls: Type[ConnectorAdapter]):
    _registry.register(cls)
    return cls

# Public shortcut
def get_adapter_cls(code: str) -> Type[ConnectorAdapter]:
    return _registry.get_adapter_cls(code)

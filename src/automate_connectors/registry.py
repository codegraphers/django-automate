from __future__ import annotations

from .adapters.base import ConnectorAdapter


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, type[ConnectorAdapter]] = {}

    def register(self, adapter_cls: type[ConnectorAdapter]):
        """Register a connector adapter class."""
        self._connectors[adapter_cls.code] = adapter_cls

    def get_adapter_cls(self, code: str) -> type[ConnectorAdapter]:
        if code not in self._connectors:
            raise ValueError(f"Connector '{code}' not found")
        return self._connectors[code]


# Global Singleton
_registry = ConnectorRegistry()


def get_connector_registry() -> ConnectorRegistry:
    return _registry


def register_connector(cls: type[ConnectorAdapter]):
    _registry.register(cls)
    return cls


# Public shortcut
def get_adapter_cls(code: str) -> type[ConnectorAdapter]:
    return _registry.get_adapter_cls(code)

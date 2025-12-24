from __future__ import annotations
from typing import Any, Dict, Type, TypeVar, Generic

T = TypeVar("T")

class Registry(Generic[T]):
    """
    Thread-safe registry for plugins (Providers, Connectors, etc).
    """
    def __init__(self, name: str):
        self.name = name
        self._items: Dict[str, Type[T]] = {}

    def register(self, key: str, cls: Type[T]) -> None:
        self._items[key] = cls

    def get(self, key: str) -> Type[T] | None:
        return self._items.get(key)

    def list_keys(self) -> list[str]:
        return list(self._items.keys())

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """
    Thread-safe registry for plugins (Providers, Connectors, etc).
    """

    def __init__(self, name: str):
        self.name = name
        self._items: dict[str, type[T]] = {}

    def register(self, key: str, cls: type[T]) -> None:
        self._items[key] = cls

    def get(self, key: str) -> type[T] | None:
        return self._items.get(key)

    def list_keys(self) -> list[str]:
        return list(self._items.keys())

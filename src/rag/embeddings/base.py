"""
Base Embeddings Protocol

Defines the interface for embedding providers.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class Embeddings(Protocol):
    """Protocol for embedding models."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        ...

    @property
    def dimension(self) -> int:
        """Return dimensionality of embeddings."""
        ...

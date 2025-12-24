"""
Base Vector Store Protocol

Defines the interface for vector databases.
"""
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class SearchResult:
    """Vector search result wrapper."""
    text: str
    score: float
    source_id: str
    metadata: dict[str, Any]

class VectorStore(Protocol):
    """Protocol for vector stores."""

    def search(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        """Search similar vectors."""
        ...

    def health(self) -> dict[str, Any]:
        """Check store health."""
        ...

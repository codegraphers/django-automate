"""
Base Embeddings Protocol

Defines the interface for embedding providers.
"""
from typing import List, Protocol, runtime_checkable

@runtime_checkable
class Embeddings(Protocol):
    """Protocol for embedding models."""
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        ...

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        ...
    
    @property
    def dimension(self) -> int:
        """Return dimensionality of embeddings."""
        ...

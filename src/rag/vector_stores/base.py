"""
Base Vector Store Protocol

Defines the interface for vector databases.
"""
from typing import List, Protocol, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Vector search result wrapper."""
    text: str
    score: float
    source_id: str
    metadata: Dict[str, Any]

class VectorStore(Protocol):
    """Protocol for vector stores."""
    
    def search(
        self, 
        embedding: List[float], 
        top_k: int, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search similar vectors."""
        ...
        
    def health(self) -> Dict[str, Any]:
        """Check store health."""
        ...

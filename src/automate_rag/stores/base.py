from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class IndexSpec:
    metric: str = "cosine" # cosine, ip, l2
    dim: int = 1536
    params: dict[str, Any] | None = None

@dataclass
class VectorUpsert:
    id: str # typically chunk_id
    vector: list[float]
    metadata: dict[str, Any]

@dataclass
class VectorHit:
    id: str
    score: float
    metadata: dict[str, Any]

class VectorStore(Protocol):
    name: str

    def ensure_index(self, *, tenant_id: str, corpus_id: str, spec: IndexSpec) -> None:
        """Create or validate index for a tenant/corpus."""
        ...

    def upsert(
        self,
        *,
        tenant_id: str,
        corpus_id: str,
        vectors: list[VectorUpsert]
    ) -> None:
        """Insert or update vectors."""
        ...

    def query(
        self,
        *,
        tenant_id: str,
        corpus_id: str,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> list[VectorHit]:
        """Search for similar vectors."""
        ...

    def delete_by_document(self, *, tenant_id: str, corpus_id: str, document_id: str) -> None:
        """Delete all vectors associated with a document."""
        ...

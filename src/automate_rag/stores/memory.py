import math
from typing import Any

from .base import IndexSpec, VectorHit, VectorStore, VectorUpsert


class MemoryVectorStore(VectorStore):
    name = "memory"

    def __init__(self):
        # tenant -> corpus -> chunk_id -> VectorUpsert
        self._data: dict[str, dict[str, dict[str, VectorUpsert]]] = {}

    def ensure_index(self, *, tenant_id: str, corpus_id: str, spec: IndexSpec) -> None:
        if tenant_id not in self._data:
            self._data[tenant_id] = {}
        if corpus_id not in self._data[tenant_id]:
            self._data[tenant_id][corpus_id] = {}

    def upsert(
        self,
        *,
        tenant_id: str,
        corpus_id: str,
        vectors: list[VectorUpsert]
    ) -> None:
        self.ensure_index(tenant_id=tenant_id, corpus_id=corpus_id, spec=IndexSpec())
        corpus_data = self._data[tenant_id][corpus_id]

        for v in vectors:
            corpus_data[v.id] = v

    def query(
        self,
        *,
        tenant_id: str,
        corpus_id: str,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> list[VectorHit]:
        if tenant_id not in self._data or corpus_id not in self._data[tenant_id]:
            return []

        corpus_data = self._data[tenant_id][corpus_id]
        scores = []

        target_norm = math.sqrt(sum(x*x for x in vector))

        for vid, item in corpus_data.items():
            # Apply filters (basic equality check logic)
            if filters:
                match = True
                for k, val in filters.items():
                    if item.metadata.get(k) != val:
                        match = False
                        break
                if not match:
                    continue

            # Cosine Sim
            dot = sum(a*b for a, b in zip(vector, item.vector, strict=False))
            item_norm = math.sqrt(sum(x*x for x in item.vector))

            score = 0.0 if target_norm * item_norm == 0 else dot / (target_norm * item_norm)

            scores.append(VectorHit(id=vid, score=score, metadata=item.metadata))

        # Sort desc
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:top_k]

    def delete_by_document(self, *, tenant_id: str, corpus_id: str, document_id: str) -> None:
        if tenant_id not in self._data or corpus_id not in self._data[tenant_id]:
            return

        corpus_data = self._data[tenant_id][corpus_id]
        to_delete = []
        for vid, item in corpus_data.items():
            if item.metadata.get("document_id") == document_id:
                to_delete.append(vid)

        for vid in to_delete:
            del corpus_data[vid]

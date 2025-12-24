"""
Milvus Vector Store Adapter
Using pymilvus
"""
import logging
from typing import List, Dict, Any, Optional
from .base import VectorStore, SearchResult

logger = logging.getLogger(__name__)

# Lazy import
try:
    from pymilvus import MilvusClient, DataType
except ImportError:
    MilvusClient = None

class MilvusStore(VectorStore):
    """Milvus / Zilliz Cloud adapter."""
    
    def __init__(self, uri: str, token: str = "", collection_name: str = "default"):
        if not MilvusClient:
            raise ImportError("pymilvus is not installed")
        
        self.uri = uri
        self.client = MilvusClient(uri=uri, token=token)
        self.collection_name = collection_name
        self._ensure_collection()
        
    def _ensure_collection(self):
        # In a real impl, we'd check if exists, or assume created by IndexProvider
        pass
        
    def search(
        self, 
        embedding: List[float], 
        top_k: int, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        
        search_params = {
            "metric_type": "COSINE",
            "params": {}
        }
        
        # filters in Milvus are expressions like "id > 0"
        # For now, we ignore dict filters or need a translator
        # This is a naive implementation
        filter_expr = ""
        if filters:
             # Basic implementation: simple equality checks
             exprs = []
             for k, v in filters.items():
                 if isinstance(v, str):
                     exprs.append(f"{k} == '{v}'")
                 else:
                     exprs.append(f"{k} == {v}")
             filter_expr = " and ".join(exprs)

        res = self.client.search(
            collection_name=self.collection_name,
            data=[embedding],
            limit=top_k,
            filter=filter_expr if filter_expr else "",
            output_fields=["text", "source_id", "metadata"]
        )
        
        # Milvus returns list of lists (one per query vector)
        if not res:
            return []
            
        hits = res[0]
        results = []
        for hit in hits:
            entity = hit.get('entity', {})
            results.append(SearchResult(
                text=entity.get('text', ''),
                score=hit.get('distance', 0.0), # or score
                source_id=entity.get('source_id', str(hit.get('id', ''))),
                metadata=entity.get('metadata', {})
            ))
            
        return results

    def health(self) -> Dict[str, Any]:
        try:
            # Simple check
            self.client.get_collection_stats(self.collection_name)
            return {"healthy": True, "message": "Connected to Milvus"}
        except Exception as e:
            return {"healthy": False, "message": str(e)}

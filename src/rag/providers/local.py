"""
Local Index Retrieval Provider

Uses internal EmbeddingModels and VectorStores to execute retrieval.
Configured in KnowledgeSource.config:
{
    "vector_store": "milvus",
    "milvus_uri": "...",
    "collection": "...",
    "embedding_model": "slug-of-model"
}
"""
import logging
from typing import Dict, Any, List

from .base import RetrievalProvider, RetrievalResult, HealthStatus, QueryContext
from rag.models import EmbeddingModel
from rag.embeddings.openai import OpenAIEmbeddings
from rag.vector_stores.milvus import MilvusStore
from rag.vector_stores.pgvector import PGVectorStore
from rag.security.secrets import resolve_secret_ref

logger = logging.getLogger(__name__)

class LocalRetrievalProvider:
    """
    Retrieval provider that uses local/internal resources.
    1. Embeds query using EmbeddingModel
    2. Searches configured VectorStore
    """
    
    key = "local_index"
    name = "Local Index (Milvus/PGVector)"
    
    def query(
        self,
        *,
        query: str,
        filters: Dict[str, Any],
        top_k: int,
        ctx: QueryContext
    ) -> RetrievalResult:
        
        # 1. Get Embedding Model
        model_key = ctx.source_config.get("embedding_model")
        if not model_key:
            # Fallback to default
            model = EmbeddingModel.objects.filter(is_default=True).first()
        else:
            model = EmbeddingModel.objects.filter(key=model_key).first()
            
        if not model:
            raise ValueError(f"No valid embedding model found (key={model_key})")
            
        # Initialize Embedder
        # TODO: Factory pattern for other providers
        api_key = resolve_secret_ref(model.credentials_ref)
        embedder = OpenAIEmbeddings(
            api_key=api_key,
            model=model.config.get("model_name", "text-embedding-ada-002"),
            api_base=model.config.get("api_base")
        )
        
        # 2. Embed Query
        vector = embedder.embed_query(query)
        
        # 3. Get Vector Store
        store_type = ctx.source_config.get("vector_store", "milvus")
        if store_type == "milvus":
            uri = ctx.source_config.get("milvus_uri") or resolve_secret_ref(ctx.source_config.get("milvus_uri_ref"))
            token = resolve_secret_ref(ctx.source_config.get("milvus_token_ref", ""))
            collection = ctx.source_config.get("collection_name", "default")
            
            store = MilvusStore(uri=uri, token=token, collection_name=collection)
            
        elif store_type == "pgvector":
            table = ctx.source_config.get("table_name", "rag_vectors")
            store = PGVectorStore(table_name=table)
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")
            
        # 4. Execute Search
        results = store.search(embedding=vector, top_k=top_k, filters=filters)
        
        # 5. Format Results
        return RetrievalResult(
            results=[{
                "text": r.text,
                "score": r.score,
                "source_id": r.source_id,
                "metadata": r.metadata
            } for r in results],
            latency_ms=0, # Calculated by caller usually
            trace_id=ctx.trace_id,
            total_count=len(results)
        )
    
    def health(self, *, ctx: QueryContext) -> HealthStatus:
        # Check vector store health
        try:
             # Basic connectivity check logic similar to query but without embedding
             store_type = ctx.source_config.get("vector_store", "milvus")
             if store_type == "milvus":
                 uri = ctx.source_config.get("milvus_uri") or resolve_secret_ref(ctx.source_config.get("milvus_uri_ref"))
                 store = MilvusStore(uri=uri) # minimal init
                 health = store.health()
             elif store_type == "pgvector":
                  store = PGVectorStore("test")
                  health = store.health()
             else:
                 return HealthStatus(healthy=False, message="Unknown store config")
                 
             return HealthStatus(healthy=health["healthy"], message=health["message"])
             
        except Exception as e:
            return HealthStatus(healthy=False, message=str(e))
            
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if not config.get("vector_store"):
            errors.append("vector_store is required")
        return errors

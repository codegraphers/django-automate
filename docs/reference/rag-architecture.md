# RAG Subsystem Architecture

This document clarifies the two RAG packages in Django Automate.

---

## Package Overview

| Package | Purpose | Status |
|---------|---------|--------|
| `rag/` | **Canonical runtime** - retrieval providers, embeddings, vector stores, SSRF-safe client | ✅ Shipped in v1 |
| `automate_rag/` | **V2 RAG models** - Corpus, Document, Chunk for document management | ⚠️ Not shipped (internal dev)

---

## rag/ (Canonical RAG Runtime)

The full-featured RAG subsystem providing:

- **Providers**: Retrieval strategies (local, external)
- **Embeddings**: OpenAI and extensible embedding backends  
- **Vector Stores**: Milvus, PGVector adapters
- **Security**: SSRF-safe HTTP client for external fetches
- **Models**: EmbeddingModel, KnowledgeSource, RAGEndpoint, RAGQueryLog
- **API**: REST endpoints for RAG queries

```python
# Example usage
from rag.models import RAGEndpoint
from rag.providers.registry import get_retrieval_provider
from rag.security.ssrf_client import ssrf_safe_request
```

---

## automate_rag/ (Document Models)

Simpler package focused on document management:

- **Models**: Corpus, Document, Chunk
- **Service**: Basic RAG service layer
- **Stores**: Document storage abstractions

```python
# Example usage
from automate_rag.models import Corpus, Document, Chunk
```

---

## When to Use Which

| Use Case | Package |
|----------|---------|
| Implementing RAG queries/retrieval | `rag/` |
| Adding new embedding providers | `rag/embeddings/` |
| Adding new vector stores | `rag/vector_stores/` |
| Building document ingestion pipelines | `automate_rag/` |
| Managing corpus/chunks | `automate_rag/` |

---

## Integration with DataChat

DataChat (`automate_datachat/`) uses **both** packages:
- `rag.models` for RAG endpoints and query logging
- `automate_rag.models` for document corpus management

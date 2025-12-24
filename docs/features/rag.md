# RAG Subsystem (Retrieval-Augmented Generation)

The RAG subsystem provides a unified interface for managing knowledge sources and creating high-performance retrieval APIs. It creates an abstraction layer over various retrieval backends, allowing you to switch between external services and local vector stores without changing your application code.

## 🏗 Architecture

The system is built on a **Provider Pattern**:

1.  **Knowledge Sources**: Define *where* data lives (e.g., External Service, Milvus, Postgres).
2.  **RAG Endpoints**: Define *how* to query it. Each endpoint has a unique slug and access control policy.
3.  **Retrieval Providers**: Handle the execution logic (HTTP proxy, Vector Search, etc.).

## 🚀 Quickstart

### 1. External Gateway (Proxy)

Use this mode to securely proxy queries to an existing RAG microservice.

1.  **Create Knowledge Source**:
    *   **Type**: `External RAG Service`
    *   **Config**: `{"base_url": "https://my-rag-service.com"}`
    *   **Credentials**: `env://MY_SERVICE_API_KEY`

2.  **Create RAG Endpoint**:
    *   **Slug**: `my-service-proxy`
    *   **Source**: Link to the source created above.

3.  **Query**:
    ```bash
    POST /api/rag/my-service-proxy/query
    { "query": "hello", "top_k": 3 }
    ```

### 2. Local Indexing (Native)

Use this mode to run RAG entirely within Django using **Milvus** or **PGVector**.

#### Step A: Configure Embedding Model
Go to **Admin > RAG > Embedding Models**:
*   **Name**: `OpenAI Ada 002`
*   **Key**: `openai-ada-002`
*   **Provider**: `OpenAI`
*   **Config**: `{"model_name": "text-embedding-ada-002"}`
*   **Credentials**: `env://OPENAI_API_KEY`

#### Step B: Create Knowledge Source
Go to **Admin > RAG > Knowledge Sources**:
*   **Type**: `Local Index (Milvus/PGVector)`
*   **Config (Milvus)**:
    ```json
    {
        "vector_store": "milvus",
        "milvus_uri": "http://localhost:19530",
        "collection_name": "my_docs",
        "embedding_model": "openai-ada-002"
    }
    ```
    *OR*
    **Config (PGVector)**:
    ```json
    {
        "vector_store": "pgvector",
        "table_name": "my_vector_table",
        "embedding_model": "openai-ada-002"
    }
    ```

#### Step C: Query
Create an endpoint pointing to this source and query it normally. The system automatically:
1.  Embeds the query using the configured model.
2.  Searches the vector store.
3.  Returns normalized results.

## 🛡 Security

### SSRF Protection
All external requests (Webhooks, RAG Proxy) go through a hardened HTTP client that:
*   **Blocks Private IPs**: Prevents access to `localhost`, `127.0.0.1`, `169.254.x.x`, etc.
*   **Disables Redirects**: Prevents redirect-based SSRF attacks.
*   **Enforces Timeouts**: Defaults to 30s.
*   **Limits Response Size**: Prevents DoS via large payloads.

### Secret Management
Never store raw secrets in configuration. Use **SecretRef**:
*   `env://VAR_NAME`: Read from environment variable.
*   `db://secret_name`: Read from `SecretStore` model.

### Access Control (RBAC)
RAG Endpoints support granular access policies:

```json
{
    "require_authenticated": true,
    "allowed_groups": ["rag_users", "staff"],
    "allowed_users": ["admin@example.com"],
    "denied_users": ["abuser@example.com"]
}
```

## 📊 Observability

### Query Logs
Every query is logged to `RAGQueryLog` with:
*   **Trace ID**: Unique correlation ID for the request.
*   **Latency**: End-to-end execution time.
*   **Results Metadata**: Source IDs and scores (content is not logged by default for privacy).
*   **Policy Decisions**: Why a request was allowed or denied.

### Test Query UI
Admin staff can test connections directly from the dashboard:
1.  Go to **RAG Endpoints**.
2.  Click an endpoint.
3.  Use the **"Test Query"** tab to run live searches and view raw JSON responses.

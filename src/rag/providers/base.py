"""
RAG Provider Interfaces

Defines the protocol/contracts for:
- RetrievalProvider: Query execution
- SourceProvider: Document fetching (Phase 2)
- IndexProvider: Indexing operations (Phase 2)
"""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class RetrievalResult:
    """Standard result from a retrieval query."""

    results: list[dict[str, Any]]  # [{text, score, source_id, metadata}]
    latency_ms: int = 0
    trace_id: str = ""
    total_count: int = 0  # Total matches (before top_k)

    def to_dict(self):
        return {
            "results": self.results,
            "latency_ms": self.latency_ms,
            "trace_id": self.trace_id,
            "total_count": self.total_count,
        }


@dataclass
class HealthStatus:
    """Health check result."""

    healthy: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"healthy": self.healthy, "message": self.message, "details": self.details}


@dataclass
class QueryContext:
    """Context passed to providers during query execution."""

    trace_id: str
    user: str
    endpoint_slug: str
    source_config: dict[str, Any]
    credentials_ref: str
    retrieval_config: dict[str, Any]


@runtime_checkable
class RetrievalProvider(Protocol):
    """
    Protocol for retrieval providers.

    Implementations must provide:
    - key: Unique identifier for this provider
    - query(): Execute a retrieval query
    - health(): Check provider health
    """

    key: str
    name: str

    def query(self, *, query: str, filters: dict[str, Any], top_k: int, ctx: QueryContext) -> RetrievalResult:
        """
        Execute a retrieval query.

        Args:
            query: The search query string
            filters: Key-value filters (namespace, tags, etc.)
            top_k: Maximum results to return
            ctx: Query context with config and credentials

        Returns:
            RetrievalResult with matching documents
        """
        ...

    def health(self, *, ctx: QueryContext) -> HealthStatus:
        """
        Check provider health.

        Returns:
            HealthStatus indicating if provider is operational
        """
        ...

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """
        Validate provider-specific configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        ...


# Future Phase 2 interfaces (stubs)


@runtime_checkable
class SourceProvider(Protocol):
    """Protocol for document source providers (Phase 2)."""

    key: str
    name: str

    def list_documents(self, *, ctx: Any, cursor: str | None = None) -> Any: ...

    def fetch_document(self, *, ctx: Any, doc_id: str) -> Any: ...


@runtime_checkable
class IndexProvider(Protocol):
    """Protocol for index providers (Phase 2)."""

    key: str
    name: str

    def index_documents(self, *, ctx: Any, documents: list[Any]) -> Any: ...

    def delete_documents(self, *, ctx: Any, doc_ids: list[str]) -> Any: ...

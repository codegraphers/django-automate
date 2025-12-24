"""
External RAG Retrieval Provider

Proxies retrieval queries to an external RAG microservice via HTTP.
This is the fastest path to value - no indexing needed in Django.
"""
import logging
import time
from typing import Any

from rag.security.ssrf_client import SSRFError, ssrf_safe_request

from .base import HealthStatus, QueryContext, RetrievalResult

logger = logging.getLogger(__name__)


class ExternalRetrievalProvider:
    """
    Retrieval provider that proxies to an external RAG microservice.
    
    Expected external API contract:
    
    POST /query
        Body: { query, top_k, filters, namespace, trace_id }
        Returns: { results: [{text, score, source_id, metadata}], latency_ms }
    
    GET /health
        Returns: { status: "ok" | "error", message: "..." }
    """

    key = "external_rag"
    name = "External RAG Service"

    def query(
        self,
        *,
        query: str,
        filters: dict[str, Any],
        top_k: int,
        ctx: QueryContext
    ) -> RetrievalResult:
        """Execute retrieval query against external service."""

        base_url = ctx.source_config.get("base_url", "").rstrip("/")
        query_path = ctx.source_config.get("query_path", "/query")
        namespace = ctx.source_config.get("namespace", "")

        if not base_url:
            raise ValueError("External RAG source requires 'base_url' in config")

        url = f"{base_url}{query_path}"

        payload = {
            "query": query,
            "top_k": top_k,
            "filters": filters,
            "namespace": namespace,
            "trace_id": ctx.trace_id
        }

        # Add any custom headers from config
        custom_headers = ctx.source_config.get("headers", {})

        start = time.time()

        try:
            response = ssrf_safe_request(
                "POST",
                url,
                json=payload,
                credentials_ref=ctx.credentials_ref,
                timeout=ctx.retrieval_config.get("timeout", 30),
                headers=custom_headers
            )

            latency = int((time.time() - start) * 1000)

            results = response.get("results", [])

            return RetrievalResult(
                results=results,
                latency_ms=response.get("latency_ms", latency),
                trace_id=ctx.trace_id,
                total_count=response.get("total_count", len(results))
            )

        except SSRFError as e:
            logger.error(f"SSRF blocked for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"External RAG query failed: {e}")
            raise

    def health(self, *, ctx: QueryContext) -> HealthStatus:
        """Check external service health."""

        base_url = ctx.source_config.get("base_url", "").rstrip("/")
        health_path = ctx.source_config.get("health_path", "/health")

        if not base_url:
            return HealthStatus(healthy=False, message="No base_url configured")

        url = f"{base_url}{health_path}"

        try:
            response = ssrf_safe_request(
                "GET",
                url,
                credentials_ref=ctx.credentials_ref,
                timeout=5
            )

            status = response.get("status", "unknown")
            return HealthStatus(
                healthy=status == "ok",
                message=response.get("message", ""),
                details=response
            )

        except Exception as e:
            return HealthStatus(
                healthy=False,
                message=str(e)
            )

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate external RAG configuration."""
        errors = []

        if not config.get("base_url"):
            errors.append("base_url is required")

        base_url = config.get("base_url", "")
        if base_url and not base_url.startswith(("http://", "https://")):
            errors.append("base_url must start with http:// or https://")

        return errors

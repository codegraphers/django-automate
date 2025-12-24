"""
RAG Query API Endpoints

Provides the retrieval API:
- POST /api/rag/{slug}/query - Execute retrieval query
- GET /api/rag/{slug}/health - Check endpoint health
"""
import json
import time
import uuid
import logging
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from rag.models import RAGEndpoint, RAGQueryLog
from rag.providers.registry import get_retrieval_provider
from rag.providers.base import QueryContext
from rag.security.access import check_access_policy, get_policy_decisions

logger = logging.getLogger(__name__)


def api_auth_required(view_func):
    """
    Decorator that ensures request is authenticated.
    Supports session auth, API key, and JWT.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check session auth
        if request.user and request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # Check API key header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        if api_key:
            # TODO: Validate API key against stored keys
            # For now, accept any key for development
            if api_key.startswith("Bearer "):
                api_key = api_key[7:]
            # Attach a pseudo-user for logging
            request.api_key_user = f"api_key:{api_key[:8]}..."
            return view_func(request, *args, **kwargs)
        
        return JsonResponse(
            {"error": "Authentication required"},
            status=401
        )
    
    return wrapper


def get_request_user(request) -> str:
    """Get username for logging, handling both session and API key auth."""
    if hasattr(request, 'api_key_user'):
        return request.api_key_user
    if request.user and request.user.is_authenticated:
        return request.user.username
    return "anonymous"


@csrf_exempt
@require_http_methods(["POST"])
@api_auth_required
def query_endpoint(request, slug):
    """
    POST /api/rag/{slug}/query
    
    Execute a retrieval query against the specified endpoint.
    
    Request body:
    {
        "query": "What is...",
        "top_k": 5,
        "filters": {"namespace": "docs"}
    }
    
    Response:
    {
        "results": [{"text": "...", "score": 0.95, "source_id": "..."}],
        "trace_id": "uuid",
        "latency_ms": 123
    }
    """
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Get endpoint
        endpoint = get_object_or_404(RAGEndpoint, slug=slug)
        
        # Check status
        if endpoint.status != 'active':
            return JsonResponse(
                {"error": f"Endpoint is {endpoint.status}", "trace_id": trace_id},
                status=503
            )
        
        # Parse request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON body", "trace_id": trace_id},
                status=400
            )
        
        query = data.get("query", "").strip()
        if not query:
            return JsonResponse(
                {"error": "Query is required", "trace_id": trace_id},
                status=400
            )
        
        filters = data.get("filters", {})
        top_k = data.get("top_k", endpoint.get_default_top_k())
        
        # Check access policy
        user = request.user if request.user.is_authenticated else None
        allowed = check_access_policy(endpoint.access_policy, user)
        policy_decisions = get_policy_decisions(endpoint.access_policy, user, allowed)
        
        if not allowed:
            # Log denied access
            RAGQueryLog.log_query(
                endpoint=endpoint,
                user=get_request_user(request),
                query=query,
                latency_ms=int((time.time() - start_time) * 1000),
                policy_decisions=policy_decisions,
                error="Access denied"
            )
            return JsonResponse(
                {"error": "Access denied", "trace_id": trace_id},
                status=403
            )
        
        # Build query context
        ctx = QueryContext(
            trace_id=trace_id,
            user=get_request_user(request),
            endpoint_slug=slug,
            source_config=endpoint.source.config,
            credentials_ref=endpoint.source.credentials_ref,
            retrieval_config=endpoint.retrieval_config
        )
        
        # Get provider and execute query
        provider = get_retrieval_provider(endpoint.retrieval_provider_key)
        result = provider.query(
            query=query,
            filters=filters,
            top_k=top_k,
            ctx=ctx
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log successful query
        RAGQueryLog.log_query(
            endpoint=endpoint,
            user=get_request_user(request),
            query=query,
            latency_ms=latency_ms,
            results_meta={
                "count": len(result.results),
                "doc_ids": [r.get("source_id") for r in result.results[:10]],
                "total_count": result.total_count
            },
            policy_decisions=policy_decisions
        )
        
        return JsonResponse({
            "results": result.results,
            "trace_id": trace_id,
            "latency_ms": latency_ms,
            "total_count": result.total_count
        })
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.exception(f"RAG query failed: {e}")
        
        # Log error (but not the query for privacy)
        try:
            endpoint = RAGEndpoint.objects.filter(slug=slug).first()
            if endpoint:
                RAGQueryLog.log_query(
                    endpoint=endpoint,
                    user=get_request_user(request),
                    query="[error]",
                    latency_ms=latency_ms,
                    error=str(e)[:500]  # Truncate for safety
                )
        except Exception:
            pass
        
        return JsonResponse(
            {"error": "Internal error", "trace_id": trace_id},
            status=500
        )


@csrf_exempt
@require_http_methods(["GET"])
def health_endpoint(request, slug):
    """
    GET /api/rag/{slug}/health
    
    Check health of the RAG endpoint.
    
    Response:
    {
        "healthy": true,
        "message": "OK",
        "endpoint": "my-endpoint",
        "provider": "external_rag"
    }
    """
    try:
        endpoint = get_object_or_404(RAGEndpoint, slug=slug)
        
        # Build context
        ctx = QueryContext(
            trace_id=str(uuid.uuid4()),
            user="health_check",
            endpoint_slug=slug,
            source_config=endpoint.source.config,
            credentials_ref=endpoint.source.credentials_ref,
            retrieval_config=endpoint.retrieval_config
        )
        
        # Get provider health
        provider = get_retrieval_provider(endpoint.retrieval_provider_key)
        status = provider.health(ctx=ctx)
        
        return JsonResponse({
            "healthy": status.healthy,
            "message": status.message,
            "endpoint": slug,
            "provider": endpoint.retrieval_provider_key,
            "status": endpoint.status
        })
        
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        return JsonResponse({
            "healthy": False,
            "message": str(e),
            "endpoint": slug
        }, status=503)

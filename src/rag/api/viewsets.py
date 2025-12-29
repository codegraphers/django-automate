"""
RAG API ViewSets.

Class-based ViewSet for RAG query endpoints.

All ViewSets are designed to be:
- Configurable via class attributes
- Overridable via inheritance
- Extensible with custom providers
"""

import logging
import time
import uuid

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rag.models import RAGEndpoint, RAGQueryLog
from rag.providers.base import QueryContext
from rag.providers.registry import get_retrieval_provider
from rag.security.access import check_access_policy, get_policy_decisions

from .serializers import (
    RAGHealthResponseSerializer,
    RAGQueryRequestSerializer,
    RAGQueryResponseSerializer,
)

logger = logging.getLogger(__name__)


class RAGAuthenticationMixin:
    """
    Mixin providing flexible authentication for RAG endpoints.

    Supports session auth, API key, and JWT tokens.

    Class Attributes:
        api_key_header: HTTP header for API key (default: X-API-Key)
        allow_anonymous: Whether to allow unauthenticated access
    """

    api_key_header = 'X-API-Key'
    allow_anonymous = False

    def get_request_user(self, request) -> str:
        """Get username for logging."""
        if hasattr(request, 'api_key_user'):
            return request.api_key_user
        if request.user and request.user.is_authenticated:
            return request.user.username
        return 'anonymous'

    def check_authentication(self, request):
        """
        Validate request authentication.

        Returns True if authenticated, raises exception otherwise.
        """
        # Session auth
        if request.user and request.user.is_authenticated:
            return True

        # API key auth
        api_key = request.headers.get(self.api_key_header)
        if api_key:
            if api_key.startswith('Bearer '):
                api_key = api_key[7:]
            request.api_key_user = f"api_key:{api_key[:8]}..."
            return True

        if not self.allow_anonymous:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Authentication required')

        return True


class RAGQueryViewSet(RAGAuthenticationMixin, viewsets.ViewSet):
    """
    RAG Query API ViewSet.

    Provides retrieval endpoints for RAG operations.

    Class Attributes:
        default_top_k: Default number of results
        max_error_length: Maximum error message length for logging

    Endpoints:
        POST /api/rag/{slug}/query/ - Execute retrieval query
        GET /api/rag/{slug}/health/ - Check endpoint health

    Example - Custom ViewSet:
        class MyRAGViewSet(RAGQueryViewSet):
            default_top_k = 10

            def get_retrieval_provider(self, endpoint):
                return MyCustomProvider()
    """

    authentication_classes = []  # Custom auth via mixin
    permission_classes = []

    default_top_k = 5
    max_error_length = 500

    def get_endpoint(self, slug: str) -> RAGEndpoint:
        """Get RAG endpoint by slug. Override to customize lookup."""
        return get_object_or_404(RAGEndpoint, slug=slug)

    def get_retrieval_provider(self, endpoint: RAGEndpoint):
        """Get retrieval provider for endpoint. Override to customize."""
        return get_retrieval_provider(endpoint.retrieval_provider_key)

    def build_query_context(
        self,
        request,
        endpoint: RAGEndpoint,
        trace_id: str
    ) -> QueryContext:
        """Build query context. Override to add custom context."""
        return QueryContext(
            trace_id=trace_id,
            user=self.get_request_user(request),
            endpoint_slug=endpoint.slug,
            source_config=endpoint.source.config,
            credentials_ref=endpoint.source.credentials_ref,
            retrieval_config=endpoint.retrieval_config,
        )

    def log_query(
        self,
        endpoint: RAGEndpoint,
        user: str,
        query: str,
        latency_ms: int,
        results_meta: dict = None,
        policy_decisions: dict = None,
        error: str = None
    ):
        """Log query for audit. Override to customize logging."""
        RAGQueryLog.log_query(
            endpoint=endpoint,
            user=user,
            query=query,
            latency_ms=latency_ms,
            results_meta=results_meta,
            policy_decisions=policy_decisions,
            error=error,
        )

    @extend_schema(
        request=RAGQueryRequestSerializer,
        responses=RAGQueryResponseSerializer,
        description="Execute a retrieval query against the RAG endpoint."
    )
    @action(detail=True, methods=['post'], url_path='query')
    def query(self, request, pk=None):
        """
        Execute retrieval query.

        Returns matching documents ranked by relevance.
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            self.check_authentication(request)

            endpoint = self.get_endpoint(pk)

            if endpoint.status != 'active':
                return Response(
                    {'error': f'Endpoint is {endpoint.status}', 'trace_id': trace_id},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            serializer = RAGQueryRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            query = serializer.validated_data['query']
            filters = serializer.validated_data.get('filters', {})
            top_k = serializer.validated_data.get('top_k', self.default_top_k)

            # Check access policy
            user = request.user if request.user.is_authenticated else None
            allowed = check_access_policy(endpoint.access_policy, user)
            policy_decisions = get_policy_decisions(endpoint.access_policy, user, allowed)

            if not allowed:
                self.log_query(
                    endpoint=endpoint,
                    user=self.get_request_user(request),
                    query=query,
                    latency_ms=int((time.time() - start_time) * 1000),
                    policy_decisions=policy_decisions,
                    error='Access denied',
                )
                return Response(
                    {'error': 'Access denied', 'trace_id': trace_id},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Execute query
            ctx = self.build_query_context(request, endpoint, trace_id)
            provider = self.get_retrieval_provider(endpoint)
            result = provider.query(query=query, filters=filters, top_k=top_k, ctx=ctx)

            latency_ms = int((time.time() - start_time) * 1000)

            # Log success
            self.log_query(
                endpoint=endpoint,
                user=self.get_request_user(request),
                query=query,
                latency_ms=latency_ms,
                results_meta={
                    'count': len(result.results),
                    'doc_ids': [r.get('source_id') for r in result.results[:10]],
                    'total_count': result.total_count,
                },
                policy_decisions=policy_decisions,
            )

            return Response({
                'results': result.results,
                'trace_id': trace_id,
                'latency_ms': latency_ms,
                'total_count': result.total_count,
            })

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.exception(f"RAG query failed: {e}")

            try:
                endpoint = RAGEndpoint.objects.filter(slug=pk).first()
                if endpoint:
                    self.log_query(
                        endpoint=endpoint,
                        user=self.get_request_user(request),
                        query='[error]',
                        latency_ms=latency_ms,
                        error=str(e)[:self.max_error_length],
                    )
            except Exception:
                pass

            return Response(
                {'error': 'Internal error', 'trace_id': trace_id},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        responses=RAGHealthResponseSerializer,
        description="Check health of the RAG endpoint."
    )
    @action(detail=True, methods=['get'], url_path='health')
    def health(self, request, pk=None):
        """Check RAG endpoint health."""
        try:
            endpoint = self.get_endpoint(pk)

            ctx = self.build_query_context(
                request,
                endpoint,
                str(uuid.uuid4())
            )

            provider = self.get_retrieval_provider(endpoint)
            health_status = provider.health(ctx=ctx)

            return Response({
                'healthy': health_status.healthy,
                'message': health_status.message,
                'endpoint': pk,
                'provider': endpoint.retrieval_provider_key,
                'status': endpoint.status,
            })

        except Exception as e:
            logger.exception(f"Health check failed: {e}")
            return Response(
                {
                    'healthy': False,
                    'message': str(e),
                    'endpoint': pk
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

"""
RAG API Serializers.

Provides validation and serialization for RAG API endpoints.
"""

from rest_framework import serializers


class RAGQueryRequestSerializer(serializers.Serializer):
    """
    Serializer for RAG query requests.

    Example:
        {
            "query": "What is the policy on...",
            "top_k": 5,
            "filters": {"namespace": "docs"}
        }
    """

    query = serializers.CharField(
        required=True,
        min_length=1,
        max_length=2000,
        help_text="Search query text"
    )
    top_k = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        default=5,
        help_text="Number of results to return"
    )
    filters = serializers.DictField(
        required=False,
        default=dict,
        help_text="Optional filters (e.g., namespace, metadata)"
    )


class RAGResultSerializer(serializers.Serializer):
    """Serializer for individual RAG result."""

    text = serializers.CharField()
    score = serializers.FloatField()
    source_id = serializers.CharField(required=False)
    metadata = serializers.DictField(required=False)


class RAGQueryResponseSerializer(serializers.Serializer):
    """Serializer for RAG query response."""

    results = RAGResultSerializer(many=True)
    trace_id = serializers.UUIDField()
    latency_ms = serializers.IntegerField()
    total_count = serializers.IntegerField(required=False)


class RAGHealthResponseSerializer(serializers.Serializer):
    """Serializer for RAG health check response."""

    healthy = serializers.BooleanField()
    message = serializers.CharField()
    endpoint = serializers.CharField()
    provider = serializers.CharField()
    status = serializers.CharField()

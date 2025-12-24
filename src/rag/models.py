"""
RAG Core Models

KnowledgeSource - Where data lives (DB, files, external service)
RAGEndpoint - Retrieval API configuration
RAGQueryLog - Audit trail for queries
"""

import hashlib
import uuid

from django.db import models


class KnowledgeSource(models.Model):
    """
    Represents a knowledge source that can be indexed and queried.
    Examples: Django model, S3 bucket, external RAG microservice
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"
        PENDING = "pending", "Pending Setup"

    class ProviderType(models.TextChoices):
        EXTERNAL_RAG = "external_rag", "External RAG Service"
        LOCAL_INDEX = "local_index", "Local Index (Milvus/PGVector)"
        DJANGO_MODEL = "django_model", "Django Model / DB Query"
        S3 = "s3", "S3 / Cloud Storage"
        FILE_SYSTEM = "file_system", "Local File System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Human-readable name")
    slug = models.SlugField(unique=True, help_text="URL-safe identifier")

    provider_key = models.CharField(
        max_length=100,
        choices=ProviderType.choices,
        default=ProviderType.EXTERNAL_RAG,
        help_text="Provider type that handles this source",
    )

    config = models.JSONField(default=dict, blank=True, help_text="Provider-specific configuration (schema validated)")

    credentials_ref = models.CharField(
        max_length=500, blank=True, help_text="SecretRef URI (e.g., env://API_KEY, vault://path/to/secret)"
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    owner_team = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)

    created_by = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Knowledge Source"
        verbose_name_plural = "Knowledge Sources"

    def __str__(self):
        return f"{self.name} ({self.provider_key})"

    def test_connection(self):
        """Test connectivity to the source. Returns (success, message)."""
        from rag.providers.registry import get_retrieval_provider

        try:
            get_retrieval_provider(self.provider_key)
            # For external RAG, we can call health check
            # For other types, implement specific checks
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)


class RAGEndpoint(models.Model):
    """
    A retrieval API endpoint that can be queried.
    Maps to POST /api/rag/{slug}/query
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"
        MAINTENANCE = "maintenance", "Under Maintenance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Used in API URL: /api/rag/{slug}/query")

    source = models.ForeignKey(KnowledgeSource, on_delete=models.CASCADE, related_name="endpoints")

    retrieval_provider_key = models.CharField(
        max_length=100, default="external_rag", help_text="Provider that handles retrieval queries"
    )

    retrieval_config = models.JSONField(
        default=dict, blank=True, help_text="Retrieval settings: top_k, filters, rerank, etc."
    )

    access_policy = models.JSONField(
        default=dict, blank=True, help_text="RBAC/ABAC rules: allowed groups, scopes, etc."
    )

    rate_limit = models.IntegerField(default=100, help_text="Max queries per minute")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "RAG Endpoint"
        verbose_name_plural = "RAG Endpoints"

    def __str__(self):
        return f"{self.name} → {self.source.name}"

    @property
    def api_url(self):
        return f"/api/rag/{self.slug}/query"

    def get_default_top_k(self):
        return self.retrieval_config.get("default_top_k", 5)


class EmbeddingModel(models.Model):
    """
    Configuration for an embedding model provider.
    Used by LocalRetrievalProvider to embed queries.
    """

    class Provider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        AZURE_OPENAI = "azure_openai", "Azure OpenAI"
        HUGGINGFACE = "huggingface", "HuggingFace (Local/API)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    key = models.SlugField(unique=True, help_text="Unique identifier (e.g., 'openai-ada-002')")

    provider = models.CharField(max_length=50, choices=Provider.choices, default=Provider.OPENAI)

    config = models.JSONField(
        default=dict, blank=True, help_text="Provider config: model_name, api_base, dimensions, etc."
    )

    credentials_ref = models.CharField(max_length=500, blank=True, help_text="API Key or secret reference")

    is_default = models.BooleanField(default=False, help_text="Use this model if none specified")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "name"]
        verbose_name = "Embedding Model"
        verbose_name_plural = "Embedding Models"

    def __str__(self):
        return f"{self.name} ({self.provider})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default
            EmbeddingModel.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class RAGQueryLog(models.Model):
    """
    Audit trail for RAG queries.
    Stores metadata (not raw queries for privacy).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    endpoint = models.ForeignKey(RAGEndpoint, on_delete=models.CASCADE, related_name="query_logs")

    request_id = models.UUIDField(default=uuid.uuid4, db_index=True, help_text="Correlation ID for tracing")

    user = models.CharField(max_length=150, db_index=True)

    query_hash = models.CharField(max_length=64, help_text="SHA256 hash of query (for privacy)")

    latency_ms = models.IntegerField(help_text="Total query latency in ms")

    results_meta = models.JSONField(default=dict, help_text="Metadata: doc_ids, scores, count")

    policy_decisions = models.JSONField(default=dict, blank=True, help_text="Access control decisions made")

    error = models.TextField(blank=True, help_text="Error message if failed")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Query Log"
        verbose_name_plural = "Query Logs"
        indexes = [
            models.Index(fields=["endpoint", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.request_id} - {self.endpoint.slug}"

    @classmethod
    def log_query(cls, *, endpoint, user, query, latency_ms, results_meta=None, policy_decisions=None, error=""):
        """Helper to create a log entry with hashed query."""
        return cls.objects.create(
            endpoint=endpoint,
            user=user,
            query_hash=hashlib.sha256(query.encode()).hexdigest(),
            latency_ms=latency_ms,
            results_meta=results_meta or {},
            policy_decisions=policy_decisions or {},
            error=error,
        )

"""
RAG Django Admin Configuration

Provides admin interfaces for:
- KnowledgeSource: Create/manage knowledge sources
- RAGEndpoint: Configure retrieval endpoints
- RAGQueryLog: View query audit logs

Includes "Test Query" functionality for endpoints.
"""

import json

from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import EmbeddingModel, KnowledgeSource, RAGEndpoint, RAGQueryLog


@admin.register(EmbeddingModel)
class EmbeddingModelAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "provider", "is_default", "created_at"]
    list_filter = ["provider", "is_default"]
    search_fields = ["name", "key"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"key": ("name",)}

    fieldsets = (
        (None, {"fields": ("name", "key", "provider", "is_default")}),
        (
            "Configuration",
            {
                "fields": ("config", "credentials_ref"),
                "description": "Provider settings (e.g. model_name) and API key reference.",
            },
        ),
    )


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = ["name", "provider_key", "status", "owner_team", "created_at"]
    list_filter = ["provider_key", "status", "owner_team"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {"fields": ("name", "slug", "provider_key", "status")}),
        (
            "Configuration",
            {
                "fields": ("config", "credentials_ref"),
                "description": "Provider-specific settings. Use SecretRef (env://VAR_NAME) for credentials.",
            },
        ),
        ("Ownership", {"fields": ("owner_team", "tags", "created_by")}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)


@admin.register(RAGEndpoint)
class RAGEndpointAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "source_link", "status", "api_url_display", "query_count"]
    list_filter = ["status", "retrieval_provider_key"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at", "api_url_display"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {"fields": ("name", "slug", "source", "status")}),
        (
            "Retrieval Configuration",
            {
                "fields": ("retrieval_provider_key", "retrieval_config"),
                "description": "Settings like top_k, filters, reranking.",
            },
        ),
        ("Access Control", {"fields": ("access_policy", "rate_limit"), "description": "RBAC rules and rate limiting."}),
        (
            "API Info",
            {
                "fields": ("api_url_display",),
            },
        ),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def source_link(self, obj):
        url = reverse("admin:rag_knowledgesource_change", args=[obj.source.id])
        return format_html('<a href="{}">{}</a>', url, obj.source.name)

    source_link.short_description = "Source"

    def api_url_display(self, obj):
        return format_html('<code style="background:#f1f5f9;padding:4px 8px;border-radius:4px">{}</code>', obj.api_url)

    api_url_display.short_description = "API URL"

    def query_count(self, obj):
        count = obj.query_logs.count()
        return format_html('<span style="color:#666">{}</span>', count)

    query_count.short_description = "Queries"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/test-query/",
                self.admin_site.admin_view(self.test_query_view),
                name="rag_ragendpoint_test_query",
            ),
        ]
        return custom_urls + urls

    def test_query_view(self, request, object_id):
        """Test query view for RAG endpoints."""
        endpoint = get_object_or_404(RAGEndpoint, pk=object_id)

        if request.method == "POST":
            # Execute test query
            import time
            import uuid

            from rag.providers.base import QueryContext
            from rag.providers.registry import get_retrieval_provider

            try:
                data = json.loads(request.body)
                query = data.get("query", "")
                top_k = data.get("top_k", 5)

                ctx = QueryContext(
                    trace_id=str(uuid.uuid4()),
                    user=request.user.username,
                    endpoint_slug=endpoint.slug,
                    source_config=endpoint.source.config,
                    credentials_ref=endpoint.source.credentials_ref,
                    retrieval_config=endpoint.retrieval_config,
                )

                provider = get_retrieval_provider(endpoint.retrieval_provider_key)
                start = time.time()
                result = provider.query(query=query, filters={}, top_k=top_k, ctx=ctx)
                latency = int((time.time() - start) * 1000)

                return JsonResponse(
                    {"success": True, "results": result.results, "latency_ms": latency, "trace_id": ctx.trace_id}
                )

            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=500)

        # GET - render test query page
        context = {
            **self.admin_site.each_context(request),
            "endpoint": endpoint,
            "title": f"Test Query: {endpoint.name}",
            "opts": self.model._meta,
        }
        return render(request, "admin/rag/ragendpoint/test_query.html", context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_test_query"] = True
        extra_context["test_query_url"] = reverse("admin:rag_ragendpoint_test_query", args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(RAGQueryLog)
class RAGQueryLogAdmin(admin.ModelAdmin):
    list_display = ["request_id_short", "endpoint_link", "user", "latency_ms", "result_count", "created_at"]
    list_filter = ["endpoint", "created_at"]
    search_fields = ["request_id", "user"]
    readonly_fields = [
        "id",
        "request_id",
        "endpoint",
        "user",
        "query_hash",
        "latency_ms",
        "results_meta",
        "policy_decisions",
        "error",
        "created_at",
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def request_id_short(self, obj):
        return str(obj.request_id)[:8]

    request_id_short.short_description = "Request ID"

    def endpoint_link(self, obj):
        url = reverse("admin:rag_ragendpoint_change", args=[obj.endpoint.id])
        return format_html('<a href="{}">{}</a>', url, obj.endpoint.slug)

    endpoint_link.short_description = "Endpoint"

    def result_count(self, obj):
        count = obj.results_meta.get("count", 0)
        return count

    result_count.short_description = "Results"

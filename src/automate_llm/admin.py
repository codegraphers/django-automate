from django.contrib import admin
from .governance.models import LLMRequest


@admin.register(LLMRequest)
class LLMRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "provider", "model", "purpose", "status", "latency_ms", "input_tokens", "output_tokens", "cost_usd", "created_at"]
    list_filter = ["status", "provider", "purpose", "created_at"]
    search_fields = ["prompt_slug", "error_message", "output_content"]
    readonly_fields = ["created_at", "input_payload", "output_content"]
    date_hierarchy = "created_at"
    
    fieldsets = [
        ("Request Info", {
            "fields": ["provider", "model", "prompt_slug", "purpose", "tenant_id"]
        }),
        ("Input/Output (for debugging)", {
            "fields": ["input_payload", "output_content"],
            "classes": ["collapse"]
        }),
        ("Usage", {
            "fields": ["input_tokens", "output_tokens", "cost_usd", "latency_ms"]
        }),
        ("Status", {
            "fields": ["status", "error_message"]
        }),
        ("Metadata", {
            "fields": ["created_at"],
            "classes": ["collapse"]
        }),
    ]

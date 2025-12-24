from django.contrib import admin
from django.utils.html import format_html

from .models import ChatEmbed, DataChatMessage, DataChatSession


@admin.register(DataChatSession)
class DataChatSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "session_key", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "session_key"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DataChatMessage)
class DataChatMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "role", "short_content", "created_at", "llm_request"]
    list_filter = ["role", "created_at"]
    search_fields = ["content"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["session", "llm_request"]

    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    short_content.short_description = "Content"


@admin.register(ChatEmbed)
class ChatEmbedAdmin(admin.ModelAdmin):
    list_display = ["name", "enabled", "api_key_preview", "domain_count", "created_at"]
    list_filter = ["enabled", "require_auth"]
    search_fields = ["name"]
    readonly_fields = ["id", "api_key", "embed_code_display", "created_at", "updated_at"]

    fieldsets = [
        (None, {
            "fields": ["name", "enabled"]
        }),
        ("Security", {
            "fields": ["api_key", "allowed_domains", "require_auth"]
        }),
        ("Limits", {
            "fields": ["rate_limit_per_minute", "max_queries_per_session", "allowed_tables"],
            "classes": ["collapse"]
        }),
        ("Customization", {
            "fields": ["theme", "welcome_message"]
        }),
        ("Embed Code", {
            "fields": ["embed_code_display"],
            "description": "Copy this code to embed the widget on your site."
        }),
    ]

    def api_key_preview(self, obj):
        return f"{obj.api_key[:12]}..." if obj.api_key else "-"
    api_key_preview.short_description = "API Key"

    def domain_count(self, obj):
        return len(obj.allowed_domains) if obj.allowed_domains else "All"
    domain_count.short_description = "Domains"

    def embed_code_display(self, obj):
        if not obj.id:
            return "Save first to generate embed code"
        code = obj.get_embed_code("https://yoursite.com")
        return format_html(
            '<textarea readonly style="width:100%; height:60px; font-family:monospace;">{}</textarea>',
            code
        )
    embed_code_display.short_description = "Embed Code"


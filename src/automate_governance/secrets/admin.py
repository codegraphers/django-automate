from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.utils.html import format_html

from .models import ConnectionProfile, StoredSecret


@admin.register(ConnectionProfile)
class ConnectionProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "is_active", "updated_at", "secrets_status_badge"]
    list_filter = ["kind", "is_active"]
    search_fields = ["name", "kind"]
    actions = ["validate_secrets"]

    def secrets_status_badge(self, obj):
        # This would optimally be computed or cached. For now, simple indicator.
        count = len(obj.secrets)
        return format_html(f"<span class='badge'>{count} refs</span>")

    secrets_status_badge.short_description = "Secrets"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/validate-secrets/",
                self.admin_site.admin_view(self.validate_secrets_view),
                name="automate_governance_connectionprofile_validate_secrets",
            ),
        ]
        return custom_urls + urls

    def validate_secrets_view(self, request, object_id, *args, **kwargs):
        # NOTE: This requires a SecretResolver instance.
        # Ideally, we inject this from settings or a service container.
        # For now, we mock/stub the interaction or rely on a global getter.
        # from automate_governance.bootstrap import get_resolver
        # resolver = get_resolver()

        # Skeleton implementation
        return JsonResponse({"status": "not_implemented_yet", "message": "Resolver injection pending"})

    @admin.action(description="Validate SecretRefs for selected profiles")
    def validate_secrets(self, request, queryset):
        # Bulk action logic
        self.message_user(request, f"Validation started for {queryset.count()} profiles.")


@admin.register(StoredSecret)
class StoredSecretAdmin(admin.ModelAdmin):
    list_display = ["namespace", "name", "version", "is_current", "created_at"]
    list_filter = ["namespace", "is_current"]
    search_fields = ["namespace", "name"]
    exclude = ["ciphertext"]
    readonly_fields = ["version", "created_at", "rotated_at"]
    actions = ["rotate_secret"]

    def rotate_secret(self, request, queryset):
        # Skeleton for rotation action
        pass

    rotate_secret.short_description = "Rotate selected secret (create new version)"

from django.contrib import admin
from django.db import models
from django.shortcuts import get_object_or_404, render
from django.urls import path
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget
from import_export.admin import ImportExportModelAdmin

from .models import ModalArtifact, ModalAuditEvent, ModalEndpoint, ModalJob, ModalProviderConfig


@admin.register(ModalProviderConfig)
class ModalProviderConfigAdmin(ImportExportModelAdmin):
    list_display = ('name', 'provider_key', 'enabled', 'created_at')
    list_filter = ('enabled', 'provider_key')
    search_fields = ('name',)

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(ModalEndpoint)
class ModalEndpointAdmin(ImportExportModelAdmin):
    list_display = ('name', 'slug', 'provider_config', 'enabled', 'test_console_link')
    list_filter = ('enabled', 'provider_config')
    search_fields = ('name', 'slug')
    readonly_fields = ('id', 'created_at', 'updated_at')

    # Enable autocomplete for provider_config (assuming it has search_fields)
    autocomplete_fields = ['provider_config']

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def test_console_link(self, obj):
        return format_html('<a href="test-console/" class="button">Test Console</a>')
    test_console_link.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/test-console/', self.admin_site.admin_view(self.test_console_view), name='modal-endpoint-test-console'),
        ]
        return custom_urls + urls

    def test_console_view(self, request, object_id):
        endpoint = get_object_or_404(ModalEndpoint, pk=object_id)
        context = dict(
            self.admin_site.each_context(request),
            endpoint=endpoint,
        )
        return render(request, "admin/automate_modal/endpoint/test_console.html", context)

@admin.register(ModalJob)
class ModalJobAdmin(ImportExportModelAdmin):
    list_display = ('job_id', 'task_type', 'endpoint', 'state', 'created_at', 'duration_display')
    list_filter = ('state', 'task_type', 'endpoint', 'created_at')
    search_fields = ('job_id', 'correlation_id', 'endpoint__slug')
    readonly_fields = ('job_id', 'correlation_id', 'scheduled_at', 'started_at', 'finished_at', 'result_summary', 'error_redacted')

    # Autocomplete for endpoint
    autocomplete_fields = ['endpoint']

    date_hierarchy = 'created_at'

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def duration_display(self, obj):
        if obj.started_at and obj.finished_at:
            return obj.finished_at - obj.started_at
        return "-"
    duration_display.short_description = "Duration"

@admin.register(ModalArtifact)
class ModalArtifactAdmin(ImportExportModelAdmin):
    list_display = ('kind', 'uri', 'size_bytes', 'created_at', 'job_link')
    list_filter = ('kind', 'created_at')
    search_fields = ('uri', 'job__job_id')
    readonly_fields = ('uri', 'size_bytes', 'sha256', 'meta')

    autocomplete_fields = ['job']

    def job_link(self, obj):
        if obj.job:
            return format_html('<a href="../../modaljob/{}/change/">{}</a>', obj.job.id, obj.job.job_id)
        return "-"
    job_link.short_description = "Job"

@admin.register(ModalAuditEvent)
class ModalAuditEventAdmin(ImportExportModelAdmin):
    list_display = ('action', 'actor_id', 'target_type', 'created_at', 'correlation_id')
    list_filter = ('action', 'target_type', 'created_at')
    search_fields = ('actor_id', 'target_id', 'correlation_id', 'request_id')
    readonly_fields = ('actor_id', 'action', 'target_type', 'target_id', 'correlation_id', 'request_id', 'meta')

    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

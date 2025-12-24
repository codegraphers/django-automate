from django.contrib import admin

from .models import InteropMapping, TemplateCollection, TemplateWorkflow


@admin.register(InteropMapping)
class InteropMappingAdmin(admin.ModelAdmin):
    list_display = ["local_workflow_id", "remote_workflow_id", "drift_state", "last_synced_at"]
    list_filter = ["drift_state", "orchestrator_instance"]
    search_fields = ["local_workflow_id", "remote_workflow_id"]
    readonly_fields = ["local_hash", "remote_hash", "last_synced_at"]


@admin.register(TemplateWorkflow)
class TemplateWorkflowAdmin(admin.ModelAdmin):
    list_display = ["name", "collection", "updated_at"]
    search_fields = ["name"]


@admin.register(TemplateCollection)
class TemplateCollectionAdmin(admin.ModelAdmin):
    list_display = ["name", "rank"]
    ordering = ["rank"]

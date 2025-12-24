from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django_json_widget.widgets import JSONEditorWidget
from django.db import models, transaction
from .models import (
    Automation, TriggerSpec, Rule, Workflow,
    Event, Outbox, Execution, ExecutionStep,
    LLMProvider, LLMModelConfig, Prompt, PromptVersion,
    Template, ConnectionProfile, PromptRelease, BudgetPolicy,
    MCPServer, MCPTool
)

import json
from django.shortcuts import render, get_object_or_404

class TriggerSpecInline(admin.StackedInline):
    model = TriggerSpec
    extra = 0
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

class RuleInline(admin.StackedInline):
    model = Rule
    extra = 0
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(TriggerSpec)
class TriggerSpecAdmin(admin.ModelAdmin):
    list_display = ["automation", "type", "is_active"]
    list_filter = ["type", "is_active", "automation"]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

class ExecutionStepInline(admin.TabularInline):
    model = ExecutionStep
    extra = 0
    # Canonical StepRun: node_key, status, started_at
    readonly_fields = ["node_key", "status", "started_at"]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ExecutionStep)
class ExecutionStepAdmin(admin.ModelAdmin):
    # Canonical StepRun
    list_display = ["execution_id", "node_key", "status", "started_at"]
    list_filter = ["status", "started_at"]
    search_fields = ["execution__id", "node_key"]
    readonly_fields = ["execution", "input_data", "output_data", "error_data", "provider_meta"]
    
    def has_add_permission(self, request):
        return False

@admin.register(Automation)
class AutomationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    # inlines = [TriggerSpecInline, RuleInline] # Rule is gone from models? RuleSpec exist.
    # We shimmed RuleSpec as Rule.
    inlines = [TriggerSpecInline, RuleInline]

    def get_urls(self):
        urls = super().get_urls()
        from .views.wizard import AutomationWizardView
        from .views.prompt_eval import PromptEvalView, prompt_test_api
        custom_urls = [
            path("wizard/", self.admin_site.admin_view(AutomationWizardView().as_view), name="automation_wizard"),
            path("prompt-eval/", self.admin_site.admin_view(PromptEvalView.as_view()), name="prompt_eval"),
            path("prompt-eval/test/", prompt_test_api, name="prompt_test_api"),
        ]
        return custom_urls + urls

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["id", "event_type", "source", "status", "created_at"]
    list_filter = ["status", "event_type", "source"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "processed_at"]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    
    def has_add_permission(self, request):
        return False

@admin.register(Execution)
class ExecutionAdmin(admin.ModelAdmin):
    list_display = ["id", "automation", "status", "started_at", "attempt"]
    list_filter = ["status", "automation"]
    ordering = ["-started_at"]
    readonly_fields = ["started_at", "finished_at", "attempt"]
    actions = ["replay_execution"]
    inlines = [ExecutionStepInline]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Replay selected executions (Safe)")
    def replay_execution(self, request, queryset):
        from automate_core.outbox.models import OutboxItem
        from django.utils import timezone
        
        success_count = 0
        with transaction.atomic():
            for execution in queryset:
                # 1. Reset State
                execution.status = "queued"
                execution.attempt = 0 # Reset attempts for fresh start
                execution.context["replay_reason"] = "admin_action"
                # Clear error state
                if "error" in execution.context:
                    del execution.context["error"]
                if "last_error" in execution.context:
                    del execution.context["last_error"]
                    
                execution.save()
                
                # 2. Enqueue in Outbox (Reliability)
                OutboxItem.objects.create(
                    tenant_id=execution.tenant_id,
                    kind="execution_queued",
                    payload={"execution_id": str(execution.id)},
                    status="PENDING",
                    priority=execution.priority,
                    created_at=timezone.now()
                )
                success_count += 1
            
        self.message_user(request, f"Reliably re-queued {success_count} executions via Outbox.")

@admin.register(PromptRelease)
class PromptReleaseAdmin(admin.ModelAdmin):
    list_display = ["prompt_version", "environment", "deployed_at", "deployed_by"]
    list_filter = ["environment"]

@admin.register(BudgetPolicy)
class BudgetPolicyAdmin(admin.ModelAdmin):
    list_display = ["name", "scope", "current_usage_cost", "max_cost_per_day_usd"]

@admin.register(LLMModelConfig)
class LLMModelConfigAdmin(admin.ModelAdmin):
    list_display = ["provider", "name", "temperature"]

@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "base_url"]

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]

@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = ["prompt", "version", "status", "created_at"]
    list_filter = ["status", "prompt"]
    readonly_fields = ["created_at"]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }



@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ["automation", "version", "is_live", "created_at"]
    list_filter = ["automation", "is_live"]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "version", "updated_at"]
    list_filter = ["type"]
    search_fields = ["name", "content"]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(ConnectionProfile)
class ConnectionProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "connector_slug", "environment", "enabled"]
    list_filter = ["connector_slug", "environment", "enabled"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["encrypted_secrets"].help_text = (
            "🔒 SECURE: Use 'env://VAR_NAME' references here. "
            "Never paste plaintext secrets in production."
        )
        return form

@admin.register(Outbox)
class OutboxAdmin(admin.ModelAdmin):
    list_display = ["id", "event_id", "status", "created_at"]
    list_filter = ["status"]
    ordering = ["created_at"]


# ============================================================================
# MCP Server Admin
# ============================================================================

class MCPToolInline(admin.TabularInline):
    model = MCPTool
    extra = 0
    readonly_fields = ["name", "description", "call_count", "last_called", "discovered_at"]
    fields = ["enabled", "name", "description", "call_count"]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MCPServer)
class MCPServerAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "endpoint_url", "auth_type", "enabled", "tool_count", "last_synced"]
    list_filter = ["enabled", "auth_type"]
    search_fields = ["name", "slug", "endpoint_url"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["last_synced", "last_error", "created_at", "updated_at"]
    inlines = [MCPToolInline]
    actions = ["sync_tools"]
    
    fieldsets = [
        (None, {
            "fields": ["name", "slug", "description", "enabled"]
        }),
        ("Connection", {
            "fields": ["endpoint_url"]
        }),
        ("Authentication", {
            "fields": ["auth_type", "auth_secret_ref", "auth_header_name"],
            "classes": ["collapse"]
        }),
        ("Status", {
            "fields": ["last_synced", "last_error"],
            "classes": ["collapse"]
        }),
    ]
    
    def tool_count(self, obj):
        return obj.tools.filter(enabled=True).count()
    tool_count.short_description = "Active Tools"
    
    @admin.action(description="Sync tools from selected servers")
    def sync_tools(self, request, queryset):
        from automate_llm.mcp_client import sync_mcp_tools, MCPClientError
        
        success = 0
        errors = []
        
        for server in queryset:
            try:
                created, updated = sync_mcp_tools(server)
                success += 1
                self.message_user(request, f"{server.name}: {created} new, {updated} updated tools")
            except MCPClientError as e:
                errors.append(f"{server.name}: {str(e)}")
        
        if errors:
            self.message_user(request, f"Errors: {'; '.join(errors)}", level="error")


@admin.register(MCPTool)
class MCPToolAdmin(admin.ModelAdmin):
    list_display = ["name", "server", "enabled", "call_count", "last_called"]
    list_filter = ["enabled", "server"]
    search_fields = ["name", "description"]
    readonly_fields = ["server", "name", "description", "input_schema", "call_count", "last_called", "discovered_at"]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }


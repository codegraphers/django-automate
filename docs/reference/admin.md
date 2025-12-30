# Admin Reference

Complete reference for all Django Automate admin classes.

## Table of Contents

1. [Base Classes](#base-classes)
2. [Mixins](#mixins)
3. [Admin Classes by Module](#admin-classes-by-module)
4. [Customization Guide](#customization-guide)

---

## Base Classes

**Import:** `from automate_core.base import BaseModelAdmin, TenantScopedAdmin`

### BaseModelAdmin

Base admin with sensible defaults and common utilities.

```python
from automate_core.base import BaseModelAdmin

@admin.register(MyModel)
class MyModelAdmin(BaseModelAdmin):
    list_display = ['name', 'status']
    search_fields = ['name']
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `list_per_page` | 25 | Records per page |
| `date_hierarchy` | `'created_at'` | Date navigation |
| `save_on_top` | True | Show save buttons at top |
| `show_timestamps` | True | Show created_at/updated_at |
| `timestamp_readonly` | True | Make timestamps read-only |

**Utility Methods:**
- `link_to_object(obj, label)`: Generate link to related object
- `colored_status(status, colors)`: Render colored status
- `truncated_field(value, max_length)`: Truncate long values

---

### TenantScopedAdmin

Admin with automatic tenant filtering.

```python
from automate_core.base import TenantScopedAdmin

@admin.register(MyTenantModel)
class MyTenantModelAdmin(TenantScopedAdmin):
    tenant_field = 'organization_id'
    show_tenant_column = True
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `tenant_field` | `'tenant_id'` | Field to filter by |
| `show_tenant_column` | False | Show tenant in list |

**Override Points:**
- `get_tenant_for_request(request)`: Custom tenant resolution

---

### AuditableModelAdmin

Admin for auditable models with audit fields.

```python
from automate_core.base import AuditableModelAdmin

@admin.register(MyAuditableModel)
class MyAuditableModelAdmin(AuditableModelAdmin):
    show_audit_fields = True
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `audit_fields` | `['created_by', ...]` | Fields to show |
| `show_audit_fields` | True | Display in list |

---

### ImportExportBaseAdmin

Admin with CSV/JSON import/export.

```python
from automate_core.base import ImportExportBaseAdmin

@admin.register(MyModel)
class MyModelAdmin(ImportExportBaseAdmin):
    export_formats = ['csv', 'json']
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `import_formats` | `['csv']` | Allowed import formats |
| `export_formats` | `['csv', 'json']` | Export format actions |

---

### SoftDeleteAdmin

Admin for soft-deletable models.

```python
from automate_core.base import SoftDeleteAdmin

@admin.register(MySoftDeleteModel)
class MySoftDeleteModelAdmin(SoftDeleteAdmin):
    show_deleted_toggle = True
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `show_deleted_toggle` | True | Show deleted toggle |
| `show_deleted_by_default` | False | Include deleted by default |

**Actions:** `restore_selected` - Restore soft-deleted records

---

### InlineBaseAdmin / StackedInlineBaseAdmin

Base inline admin classes.

```python
from automate_core.base import InlineBaseAdmin

class ItemInline(InlineBaseAdmin):
    model = Item
    fields = ['name', 'quantity']
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `extra` | 0 | Extra blank forms |
| `max_num` | 10 | Maximum forms |
| `show_change_link` | True | Link to full form |
| `can_delete` | True | Allow deletion |

---

## Mixins

### ExportMixin

Add export actions to any admin.

```python
from automate_core.base import ExportMixin, BaseModelAdmin

class MyAdmin(ExportMixin, BaseModelAdmin):
    export_formats = ['csv', 'json']
    export_fields = ['name', 'email', 'created_at']
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `export_formats` | `['csv', 'json']` | Available formats |
| `export_fields` | None | Fields to export (all if None) |
| `export_exclude` | `[]` | Fields to exclude |

---

### BulkActionsMixin

Add bulk update/delete actions.

```python
from automate_core.base import BulkActionsMixin, BaseModelAdmin

class MyAdmin(BulkActionsMixin, BaseModelAdmin):
    bulk_update_fields = ['status', 'category']
```

**Actions:**
- `bulk_update_status`: Update status field
- `bulk_enable`: Enable selected
- `bulk_disable`: Disable selected

---

### AuditMixin

Log admin actions to audit trail.

```python
from automate_core.base import AuditMixin, BaseModelAdmin

class MyAdmin(AuditMixin, BaseModelAdmin):
    audit_log_changes = True
    audit_log_model = AuditLog  # Your audit model
```

---

### SearchMixin

Enhanced search with field-specific lookups.

```python
from automate_core.base import SearchMixin, BaseModelAdmin

class MyAdmin(SearchMixin, BaseModelAdmin):
    advanced_search_fields = {
        'name': 'icontains',
        'email': 'iexact',
    }
```

---

### FilterMixin

Dynamic filter generation.

```python
from automate_core.base import FilterMixin, BaseModelAdmin

class MyAdmin(FilterMixin, BaseModelAdmin):
    auto_filters = True  # Auto-add choice/boolean filters
    date_filters = ['created_at', 'updated_at']
```

---

### PermissionMixin

Object-level permission checks.

```python
class MyAdmin(PermissionMixin, BaseModelAdmin):
    def has_change_permission(self, request, obj=None):
        if obj and obj.owner != request.user:
            return False
        return super().has_change_permission(request, obj)
```

---

## Admin Classes by Module

### automate/admin.py (17 classes)

| Admin Class | Model | Base | Key Features |
|-------------|-------|------|--------------|
| `AutomationAdmin` | Automation | TenantScopedAdmin | Workflow inlines, enable/disable action |
| `TriggerSpecAdmin` | TriggerSpec | BaseModelAdmin | Trigger config display |
| `WorkflowAdmin` | Workflow | BaseModelAdmin | Graph preview, version history |
| `ExecutionAdmin` | Execution | AuditableModelAdmin | Status filtering, step inlines |
| `ExecutionStepAdmin` | ExecutionStep | BaseModelAdmin | Input/output display |
| `EventAdmin` | Event | BaseModelAdmin | Payload preview, type filter |
| `PromptAdmin` | Prompt | BaseModelAdmin | Version inlines |
| `PromptVersionAdmin` | PromptVersion | AuditableModelAdmin | Template preview |
| `PromptReleaseAdmin` | PromptRelease | BaseModelAdmin | Deploy action |
| `LLMProviderAdmin` | LLMProvider | BaseModelAdmin | Test connection action |
| `LLMModelConfigAdmin` | LLMModelConfig | BaseModelAdmin | Provider filter |
| `BudgetPolicyAdmin` | BudgetPolicy | TenantScopedAdmin | Limit display |
| `TemplateAdmin` | Template | BaseModelAdmin | Content preview |
| `ConnectionProfileAdmin` | ConnectionProfile | TenantScopedAdmin | Credentials masked |
| `OutboxAdmin` | Outbox | BaseModelAdmin | Retry action, status filter |
| `MCPServerAdmin` | MCPServer | BaseModelAdmin | Health check, sync tools |
| `MCPToolAdmin` | MCPTool | BaseModelAdmin | Schema display |

### automate_datachat/admin.py (3 classes)

| Admin Class | Model | Base | Key Features |
|-------------|-------|------|--------------|
| `DataChatSessionAdmin` | DataChatSession | TenantScopedAdmin | User filter, message count |
| `DataChatMessageAdmin` | DataChatMessage | BaseModelAdmin | Content preview, SQL display |
| `ChatEmbedAdmin` | ChatEmbed | TenantScopedAdmin | API key regenerate, domain list |

### automate_modal/admin.py (5 classes)

| Admin Class | Model | Base | Key Features |
|-------------|-------|------|--------------|
| `ModalProviderConfigAdmin` | ModalProviderConfig | ImportExportBaseAdmin | Config validation |
| `ModalEndpointAdmin` | ModalEndpoint | ImportExportBaseAdmin | Test console link |
| `ModalJobAdmin` | ModalJob | ImportExportBaseAdmin | Status filter, cost display |
| `ModalArtifactAdmin` | ModalArtifact | ImportExportBaseAdmin | Download link |
| `ModalAuditEventAdmin` | ModalAuditEvent | ImportExportBaseAdmin | Date hierarchy |

### rag/admin.py (4 classes)

| Admin Class | Model | Base | Key Features |
|-------------|-------|------|--------------|
| `RAGEndpointAdmin` | RAGEndpoint | TenantScopedAdmin | Test query page |
| `KnowledgeSourceAdmin` | KnowledgeSource | TenantScopedAdmin | Sync action, doc count |
| `EmbeddingModelAdmin` | EmbeddingModel | BaseModelAdmin | Dimension display |
| `RAGQueryLogAdmin` | RAGQueryLog | BaseModelAdmin | Query display, latency |

### automate_interop/admin.py (3 classes)

| Admin Class | Model | Base | Key Features |
|-------------|-------|------|--------------|
| `InteropMappingAdmin` | InteropMapping | BaseModelAdmin | Platform filter |
| `TemplateCollectionAdmin` | TemplateCollection | BaseModelAdmin | Template count |
| `TemplateWorkflowAdmin` | TemplateWorkflow | BaseModelAdmin | Collection filter |

### Other Modules (4 classes)

| Admin Class | Module | Model | Base |
|-------------|--------|-------|------|
| `LLMRequestAdmin` | automate_llm | LLMRequest | AuditableModelAdmin |
| `AuditLogEntryAdmin` | automate_observability | AuditLogEntry | BaseModelAdmin |
| `ConnectionProfileAdmin` | automate_governance | ConnectionProfile | TenantScopedAdmin |
| `StoredSecretAdmin` | automate_governance | StoredSecret | BaseModelAdmin |

---

## Customization Guide

### Override Existing Admin

```python
# In your app's admin.py
from django.contrib import admin
from automate.admin import AutomationAdmin
from automate_core.workflows.models import Automation

# Unregister default
admin.site.unregister(Automation)

# Register custom
@admin.register(Automation)
class CustomAutomationAdmin(AutomationAdmin):
    list_display = ['name', 'enabled', 'department', 'created_at']
    list_filter = ['enabled', 'department']
    
    def department(self, obj):
        return obj.metadata.get('department', '-')
```

### Custom Actions

```python
@admin.register(MyModel)
class MyModelAdmin(BaseModelAdmin):
    actions = ['make_active', 'send_notification']
    
    @admin.action(description="Mark as active")
    def make_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f"Updated {updated} records")
    
    @admin.action(description="Send notification")
    def send_notification(self, request, queryset):
        for obj in queryset:
            send_email(obj.user.email, "Notification", obj.name)
        self.message_user(request, f"Sent {queryset.count()} notifications")
```

### Custom Fieldsets

```python
@admin.register(MyModel)
class MyModelAdmin(BaseModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['name', 'description']
        }),
        ('Configuration', {
            'fields': ['config', 'options'],
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ['created_at', 'updated_at', 'created_by'],
            'classes': ['collapse']
        }),
    ]
```

### Custom Change Form Template

```python
@admin.register(MyModel)
class MyModelAdmin(BaseModelAdmin):
    change_form_template = 'admin/myapp/mymodel/change_form.html'
```

```html
<!-- templates/admin/myapp/mymodel/change_form.html -->
{% extends "admin/change_form.html" %}

{% block after_field_sets %}
<div class="custom-section">
    <h2>Custom Section</h2>
    <p>Additional content here</p>
</div>
{% endblock %}
```

### Custom List Display Methods

```python
@admin.register(MyModel)
class MyModelAdmin(BaseModelAdmin):
    list_display = ['name', 'status_badge', 'item_count', 'owner_link']
    
    @admin.display(description="Status")
    def status_badge(self, obj):
        return self.colored_status(obj.status)
    
    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()
    
    @admin.display(description="Owner")
    def owner_link(self, obj):
        return self.link_to_object(obj.owner)
```

"""
Django Automate - Abstract Base Admin Classes.

Provides abstract base classes for all admin classes in Django Automate.
These bases ensure consistency, reusability, and extensibility across all admin interfaces.

Usage:
    from automate_core.admin.base import BaseModelAdmin, TenantScopedAdmin

    @admin.register(MyModel)
    class MyModelAdmin(BaseModelAdmin):
        list_display = ['name', 'created_at']

Configuration:
    All base classes support configuration via class attributes that can be
    overridden in subclasses or via Django settings.

Design Principles:
    - DRY: Common configuration defined once
    - Extensibility: All methods can be overridden
    - Configurability: Settings-driven behavior
    - Composability: Mixins can be combined freely
"""

from typing import Any, Dict, List, Optional, Tuple, Type

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe


def get_admin_setting(key: str, default: Any = None) -> Any:
    """
    Get an admin setting from Django settings.

    Looks for AUTOMATE_ADMIN dict in settings.
    """
    admin_settings = getattr(settings, 'AUTOMATE_ADMIN', {})
    return admin_settings.get(key, default)


# =============================================================================
# MIXINS
# =============================================================================


class ExportMixin:
    """
    Mixin adding export actions to admin.

    Supports CSV, JSON, and Excel export formats.

    Class Attributes:
        export_formats: List of formats to enable ('csv', 'json', 'xlsx')
        export_fields: Fields to include in export (None = all)
        export_exclude: Fields to exclude from export

    Example:
        class MyModelAdmin(ExportMixin, BaseModelAdmin):
            export_formats = ['csv', 'json']
            export_fields = ['name', 'email', 'created_at']
    """

    export_formats = ['csv', 'json']
    export_fields = None
    export_exclude = []

    def get_export_fields(self, request: HttpRequest) -> List[str]:
        """Get fields to export. Override to customize."""
        if self.export_fields:
            return self.export_fields

        model = self.model
        fields = [f.name for f in model._meta.fields]
        return [f for f in fields if f not in self.export_exclude]

    def export_as_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        """Export queryset as CSV."""
        import csv
        from django.http import HttpResponse

        fields = self.get_export_fields(request)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.model._meta.model_name}.csv"'

        writer = csv.writer(response)
        writer.writerow(fields)

        for obj in queryset:
            row = [getattr(obj, f, '') for f in fields]
            writer.writerow(row)

        return response

    export_as_csv.short_description = "Export selected as CSV"

    def export_as_json(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        """Export queryset as JSON."""
        import json
        from django.http import HttpResponse
        from django.core.serializers.json import DjangoJSONEncoder

        fields = self.get_export_fields(request)
        data = []

        for obj in queryset:
            item = {f: getattr(obj, f, None) for f in fields}
            data.append(item)

        response = HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.model._meta.model_name}.json"'
        return response

    export_as_json.short_description = "Export selected as JSON"

    def get_actions(self, request: HttpRequest) -> Dict:
        """Add export actions."""
        actions = super().get_actions(request)

        if 'csv' in self.export_formats:
            actions['export_as_csv'] = (
                self.export_as_csv,
                'export_as_csv',
                'Export selected as CSV'
            )
        if 'json' in self.export_formats:
            actions['export_as_json'] = (
                self.export_as_json,
                'export_as_json',
                'Export selected as JSON'
            )

        return actions


class BulkActionsMixin:
    """
    Mixin adding bulk update/delete actions.

    Class Attributes:
        bulk_update_fields: Fields that can be bulk updated

    Example:
        class MyModelAdmin(BulkActionsMixin, BaseModelAdmin):
            bulk_update_fields = ['status', 'category']
    """

    bulk_update_fields = []

    def bulk_update_status(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Bulk update status field."""
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            self.message_user(
                request,
                f"Updated {updated} records",
                messages.SUCCESS
            )

    bulk_update_status.short_description = "Update status for selected"

    def bulk_enable(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Bulk enable records."""
        updated = queryset.update(enabled=True)
        self.message_user(request, f"Enabled {updated} records", messages.SUCCESS)

    bulk_enable.short_description = "Enable selected"

    def bulk_disable(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Bulk disable records."""
        updated = queryset.update(enabled=False)
        self.message_user(request, f"Disabled {updated} records", messages.SUCCESS)

    bulk_disable.short_description = "Disable selected"


class AuditMixin:
    """
    Mixin for logging admin actions to audit trail.

    Class Attributes:
        audit_log_changes: If True, log all changes
        audit_log_model: Model to use for audit logging

    Example:
        class MyModelAdmin(AuditMixin, BaseModelAdmin):
            audit_log_changes = True
    """

    audit_log_changes = True
    audit_log_model = None  # Set to your audit model

    def log_change(self, request: HttpRequest, obj: Any, message: str) -> None:
        """Log a change to the audit trail."""
        super().log_change(request, obj, message)

        if self.audit_log_changes and self.audit_log_model:
            self.audit_log_model.objects.create(
                user=request.user.username,
                action='change',
                object_type=obj._meta.label,
                object_id=str(obj.pk),
                details=message,
            )

    def log_addition(self, request: HttpRequest, obj: Any, message: str) -> None:
        """Log an addition to the audit trail."""
        super().log_addition(request, obj, message)

        if self.audit_log_changes and self.audit_log_model:
            self.audit_log_model.objects.create(
                user=request.user.username,
                action='add',
                object_type=obj._meta.label,
                object_id=str(obj.pk),
                details=message,
            )

    def log_deletion(self, request: HttpRequest, obj: Any, object_repr: str) -> None:
        """Log a deletion to the audit trail."""
        super().log_deletion(request, obj, object_repr)

        if self.audit_log_changes and self.audit_log_model:
            self.audit_log_model.objects.create(
                user=request.user.username,
                action='delete',
                object_type=obj._meta.label,
                object_id=str(obj.pk),
                details=object_repr,
            )


class SearchMixin:
    """
    Mixin for enhanced search functionality.

    Class Attributes:
        advanced_search_fields: Fields with advanced search types
        search_placeholder: Placeholder text for search box

    Example:
        class MyModelAdmin(SearchMixin, BaseModelAdmin):
            advanced_search_fields = {
                'name': 'icontains',
                'email': 'iexact',
            }
    """

    advanced_search_fields = {}
    search_placeholder = "Search..."

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet,
        search_term: str
    ) -> Tuple[QuerySet, bool]:
        """Enhanced search with field-specific lookups."""
        if not search_term:
            return queryset, False

        if self.advanced_search_fields:
            from django.db.models import Q

            q_objects = Q()
            for field, lookup in self.advanced_search_fields.items():
                q_objects |= Q(**{f"{field}__{lookup}": search_term})

            return queryset.filter(q_objects), False

        return super().get_search_results(request, queryset, search_term)


class FilterMixin:
    """
    Mixin for dynamic filter generation.

    Class Attributes:
        auto_filters: If True, auto-generate filters for common fields
        date_filters: Fields to add date range filtering

    Example:
        class MyModelAdmin(FilterMixin, BaseModelAdmin):
            auto_filters = True
            date_filters = ['created_at', 'updated_at']
    """

    auto_filters = False
    date_filters = []

    def get_list_filter(self, request: HttpRequest) -> List:
        """Get list filters with optional auto-generation."""
        filters = list(super().get_list_filter(request) or [])

        if self.auto_filters:
            model = self.model
            for field in model._meta.fields:
                if field.name in filters:
                    continue
                if field.choices:
                    filters.append(field.name)
                elif field.get_internal_type() == 'BooleanField':
                    filters.append(field.name)

        return filters


class PermissionMixin:
    """
    Mixin for object-level permissions.

    Class Attributes:
        object_permission_model: Permission model for object-level checks

    Example:
        class MyModelAdmin(PermissionMixin, BaseModelAdmin):
            def has_change_permission(self, request, obj=None):
                if obj and obj.owner != request.user:
                    return False
                return super().has_change_permission(request, obj)
    """

    def has_view_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Check view permission. Override for object-level checks."""
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Check change permission. Override for object-level checks."""
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Check delete permission. Override for object-level checks."""
        return super().has_delete_permission(request, obj)


# =============================================================================
# BASE ADMIN CLASSES
# =============================================================================


class BaseModelAdmin(admin.ModelAdmin):
    """
    Abstract base admin with common configuration.

    Provides sensible defaults and extension points for all admin classes.

    Class Attributes:
        default_list_per_page: Records per page (default: 25)
        default_ordering: Default ordering (default: ['-created_at'])
        show_timestamps: If True, show created_at/updated_at in list

    Override Points:
        - get_list_display(): Customize list columns
        - get_readonly_fields(): Customize readonly fields
        - get_fieldsets(): Customize form layout
        - get_queryset(): Customize queryset filtering

    Example:
        @admin.register(MyModel)
        class MyModelAdmin(BaseModelAdmin):
            list_display = ['name', 'status', 'created_at']
            search_fields = ['name']
    """

    # Configuration
    default_list_per_page = 25
    default_ordering = ['-created_at']
    show_timestamps = True

    # Defaults
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True
    show_full_result_count = True

    # Timestamp fields (auto-added if show_timestamps=True)
    timestamp_fields = ['created_at', 'updated_at']
    timestamp_readonly = True

    def get_list_display(self, request: HttpRequest) -> List[str]:
        """Get list display fields with optional timestamps."""
        display = list(super().get_list_display(request))

        if self.show_timestamps:
            for field in self.timestamp_fields:
                if field not in display and hasattr(self.model, field):
                    display.append(field)

        return display

    def get_readonly_fields(self, request: HttpRequest, obj: Any = None) -> List[str]:
        """Get readonly fields with optional timestamp fields."""
        readonly = list(super().get_readonly_fields(request, obj))

        if self.timestamp_readonly:
            for field in self.timestamp_fields:
                if field not in readonly and hasattr(self.model, field):
                    readonly.append(field)

        return readonly

    def get_ordering(self, request: HttpRequest) -> List[str]:
        """Get ordering with default fallback."""
        ordering = super().get_ordering(request)
        if not ordering:
            return self.default_ordering
        return ordering

    # Utility methods for subclasses

    def link_to_object(self, obj: Any, label: str = None) -> str:
        """Generate a link to another object's admin page."""
        if not obj:
            return '-'
        url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=[obj.pk]
        )
        return format_html('<a href="{}">{}</a>', url, label or str(obj))

    def colored_status(self, status: str, colors: Dict[str, str] = None) -> str:
        """Render status with color."""
        default_colors = {
            'active': 'green',
            'inactive': 'gray',
            'pending': 'orange',
            'completed': 'blue',
            'failed': 'red',
            'error': 'red',
        }
        colors = colors or default_colors
        color = colors.get(status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )

    def truncated_field(self, value: str, max_length: int = 50) -> str:
        """Truncate long field values with ellipsis."""
        if not value:
            return '-'
        if len(str(value)) > max_length:
            return f"{str(value)[:max_length]}..."
        return str(value)


class TenantScopedAdmin(BaseModelAdmin):
    """
    Admin for multi-tenant models with automatic tenant filtering.

    Automatically filters queryset by tenant based on user context.

    Class Attributes:
        tenant_field: Name of the tenant field (default: 'tenant_id')
        show_tenant_column: If True, show tenant in list display

    Override Points:
        - get_tenant_for_request(): Customize tenant resolution

    Example:
        @admin.register(MyTenantModel)
        class MyTenantModelAdmin(TenantScopedAdmin):
            tenant_field = 'organization_id'
    """

    tenant_field = 'tenant_id'
    show_tenant_column = False

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Filter queryset by tenant."""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        tenant_id = self.get_tenant_for_request(request)
        if tenant_id:
            return qs.filter(**{self.tenant_field: tenant_id})

        return qs

    def get_tenant_for_request(self, request: HttpRequest) -> Optional[str]:
        """
        Get tenant ID for the current request.

        Override to customize tenant resolution.
        Default: returns None (no filtering for non-superusers).
        """
        return getattr(request.user, 'tenant_id', None)

    def get_list_display(self, request: HttpRequest) -> List[str]:
        """Optionally add tenant column."""
        display = super().get_list_display(request)

        if self.show_tenant_column and request.user.is_superuser:
            if self.tenant_field not in display:
                display = [self.tenant_field] + list(display)

        return display

    def save_model(self, request: HttpRequest, obj: Any, form: Any, change: bool) -> None:
        """Auto-set tenant on new objects."""
        if not change:
            tenant_id = self.get_tenant_for_request(request)
            if tenant_id and not getattr(obj, self.tenant_field):
                setattr(obj, self.tenant_field, tenant_id)

        super().save_model(request, obj, form, change)


class AuditableModelAdmin(AuditMixin, BaseModelAdmin):
    """
    Admin for auditable models with audit field display.

    Automatically shows audit fields and logs changes.

    Class Attributes:
        audit_fields: List of audit field names
        show_audit_fields: If True, show in list display

    Example:
        @admin.register(MyAuditableModel)
        class MyAuditableModelAdmin(AuditableModelAdmin):
            show_audit_fields = True
    """

    audit_fields = ['created_by', 'modified_by', 'created_at', 'updated_at']
    show_audit_fields = True

    def get_readonly_fields(self, request: HttpRequest, obj: Any = None) -> List[str]:
        """Make audit fields readonly."""
        readonly = list(super().get_readonly_fields(request, obj))

        for field in self.audit_fields:
            if field not in readonly and hasattr(self.model, field):
                readonly.append(field)

        return readonly

    def get_fieldsets(self, request: HttpRequest, obj: Any = None):
        """Add audit fieldset if not defined."""
        fieldsets = super().get_fieldsets(request, obj)

        if fieldsets and not any('Audit' in str(fs[0]) for fs in fieldsets):
            audit_fields = [f for f in self.audit_fields if hasattr(self.model, f)]
            if audit_fields:
                fieldsets = list(fieldsets) + [
                    ('Audit Information', {
                        'classes': ('collapse',),
                        'fields': audit_fields,
                    })
                ]

        return fieldsets


class ImportExportBaseAdmin(ExportMixin, BaseModelAdmin):
    """
    Admin with import/export functionality.

    Supports CSV and JSON import/export out of the box.

    Class Attributes:
        import_formats: List of import formats
        export_formats: List of export formats
        import_template: Template for import page

    Example:
        @admin.register(MyModel)
        class MyModelAdmin(ImportExportBaseAdmin):
            import_formats = ['csv']
            export_formats = ['csv', 'json']
    """

    import_formats = ['csv']
    export_formats = ['csv', 'json']
    import_template = None


class SoftDeleteAdmin(BaseModelAdmin):
    """
    Admin for soft-deletable models.

    Shows deleted records toggle and provides restore action.

    Class Attributes:
        show_deleted_toggle: If True, show toggle in changelist
        show_deleted_by_default: If True, show deleted records

    Example:
        @admin.register(MySoftDeleteModel)
        class MySoftDeleteModelAdmin(SoftDeleteAdmin):
            show_deleted_toggle = True
    """

    show_deleted_toggle = True
    show_deleted_by_default = False

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Include or exclude deleted based on toggle."""
        qs = super().get_queryset(request)

        show_deleted = request.GET.get('show_deleted', '')
        if show_deleted == '1' or self.show_deleted_by_default:
            return qs.model.all_objects.all()

        return qs

    def get_list_display(self, request: HttpRequest) -> List[str]:
        """Add deleted status column."""
        display = super().get_list_display(request)
        if 'is_deleted' not in display:
            display = list(display) + ['is_deleted']
        return display

    def restore_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Restore soft-deleted records."""
        for obj in queryset:
            if hasattr(obj, 'restore'):
                obj.restore()

        self.message_user(
            request,
            f"Restored {queryset.count()} records",
            messages.SUCCESS
        )

    restore_selected.short_description = "Restore selected"

    def get_actions(self, request: HttpRequest) -> Dict:
        """Add restore action."""
        actions = super().get_actions(request)
        actions['restore_selected'] = (
            self.restore_selected,
            'restore_selected',
            'Restore selected'
        )
        return actions


class InlineBaseAdmin(admin.TabularInline):
    """
    Base inline admin with common configuration.

    Class Attributes:
        default_extra: Number of extra forms (default: 0)
        default_max_num: Maximum forms (default: 10)

    Example:
        class MyInline(InlineBaseAdmin):
            model = RelatedModel
            fields = ['name', 'value']
    """

    extra = 0
    max_num = 10
    show_change_link = True
    can_delete = True

    default_extra = 0
    default_max_num = 10


class StackedInlineBaseAdmin(admin.StackedInline):
    """
    Base stacked inline admin with common configuration.

    Example:
        class MyStackedInline(StackedInlineBaseAdmin):
            model = RelatedModel
    """

    extra = 0
    max_num = 5
    show_change_link = True
    can_delete = True


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Mixins
    'ExportMixin',
    'BulkActionsMixin',
    'AuditMixin',
    'SearchMixin',
    'FilterMixin',
    'PermissionMixin',
    # Base Admin Classes
    'BaseModelAdmin',
    'TenantScopedAdmin',
    'AuditableModelAdmin',
    'ImportExportBaseAdmin',
    'SoftDeleteAdmin',
    'InlineBaseAdmin',
    'StackedInlineBaseAdmin',
    # Utilities
    'get_admin_setting',
]

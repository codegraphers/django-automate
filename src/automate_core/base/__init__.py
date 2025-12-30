"""
Django Automate - Base Classes Package.

This package provides abstract base classes for all Django Automate components:
- Models: TimeStampedModel, TenantScopedModel, AuditableModel, etc.
- Admin: BaseModelAdmin, TenantScopedAdmin, etc.
- Serializers: BaseSerializer, BaseModelSerializer, etc.

Usage:
    from automate_core.base import TimeStampedModel, BaseModelAdmin, BaseSerializer

    class MyModel(TimeStampedModel):
        name = models.CharField(max_length=200)

    @admin.register(MyModel)
    class MyModelAdmin(BaseModelAdmin):
        list_display = ['name', 'created_at']
"""

# Model base classes
from .models import (
    AuditableModel,
    CacheableMixin,
    HistoryMixin,
    MetadataModel,
    OrderedManager,
    OrderedModel,
    SignalMixin,
    SluggedModel,
    SoftDeleteManager,
    SoftDeleteModel,
    StatusManager,
    StatusModel,
    TenantManager,
    TenantScopedModel,
    TimeStampedModel,
    UUIDModel,
    ValidatableMixin,
    get_model_setting,
)

# Admin base classes
from .admin import (
    AuditableModelAdmin,
    AuditMixin,
    BaseModelAdmin,
    BulkActionsMixin,
    ExportMixin,
    FilterMixin,
    ImportExportBaseAdmin,
    InlineBaseAdmin,
    PermissionMixin,
    SearchMixin,
    SoftDeleteAdmin,
    StackedInlineBaseAdmin,
    TenantScopedAdmin,
    get_admin_setting,
)

# Serializer base classes
from .serializers import (
    AuditableSerializer,
    BaseModelSerializer,
    BaseSerializer,
    CacheMixin,
    ContextMixin,
    DynamicFieldsMixin,
    ExpandableMixin,
    NestedWritableSerializer,
    PaginationMixin,
    ReadOnlySerializer,
    TenantScopedSerializer,
    ValidationMixin,
    get_serializer_setting,
)

__all__ = [
    # Model Managers
    'SoftDeleteManager',
    'TenantManager',
    'OrderedManager',
    'StatusManager',
    # Model Base Classes
    'TimeStampedModel',
    'UUIDModel',
    'TenantScopedModel',
    'AuditableModel',
    'SoftDeleteModel',
    'OrderedModel',
    'SluggedModel',
    'StatusModel',
    'MetadataModel',
    # Model Mixins
    'HistoryMixin',
    'CacheableMixin',
    'ValidatableMixin',
    'SignalMixin',
    # Admin Mixins
    'ExportMixin',
    'BulkActionsMixin',
    'AuditMixin',
    'SearchMixin',
    'FilterMixin',
    'PermissionMixin',
    # Admin Base Classes
    'BaseModelAdmin',
    'TenantScopedAdmin',
    'AuditableModelAdmin',
    'ImportExportBaseAdmin',
    'SoftDeleteAdmin',
    'InlineBaseAdmin',
    'StackedInlineBaseAdmin',
    # Serializer Mixins
    'ValidationMixin',
    'ContextMixin',
    'DynamicFieldsMixin',
    'ExpandableMixin',
    'PaginationMixin',
    'CacheMixin',
    # Serializer Base Classes
    'BaseSerializer',
    'BaseModelSerializer',
    'TenantScopedSerializer',
    'AuditableSerializer',
    'NestedWritableSerializer',
    'ReadOnlySerializer',
    # Utilities
    'get_model_setting',
    'get_admin_setting',
    'get_serializer_setting',
]

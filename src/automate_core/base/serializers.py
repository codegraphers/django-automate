"""
Django Automate - Abstract Base Serializers.

Provides abstract base classes for all serializers in Django Automate.
These bases ensure consistency, reusability, and extensibility.

Usage:
    from automate_core.serializers.base import BaseSerializer, BaseModelSerializer

    class MySerializer(BaseSerializer):
        name = serializers.CharField()

Configuration:
    All base classes support configuration via class attributes.

Design Principles:
    - DRY: Common validation defined once
    - Extensibility: All methods can be overridden
    - Configurability: Context-aware behavior
"""

from typing import Any, Dict, List, Optional, Type

from django.conf import settings
from rest_framework import serializers


def get_serializer_setting(key: str, default: Any = None) -> Any:
    """Get a serializer setting from Django settings."""
    serializer_settings = getattr(settings, 'AUTOMATE_SERIALIZERS', {})
    return serializer_settings.get(key, default)


# =============================================================================
# MIXINS
# =============================================================================


class ValidationMixin:
    """
    Mixin for enhanced validation with custom error messages.

    Class Attributes:
        error_messages: Dict of field -> error message overrides
        strict_validation: If True, fail on unknown fields

    Example:
        class MySerializer(ValidationMixin, BaseSerializer):
            error_messages = {
                'name': {'required': 'Name is mandatory'},
            }
    """

    error_messages = {}
    strict_validation = False

    def validate(self, attrs: Dict) -> Dict:
        """Run validation with custom error handling."""
        attrs = super().validate(attrs)

        if self.strict_validation:
            self._check_unknown_fields()

        return attrs

    def _check_unknown_fields(self):
        """Check for unknown fields in input data."""
        if not hasattr(self, 'initial_data'):
            return

        known_fields = set(self.fields.keys())
        input_fields = set(self.initial_data.keys())
        unknown = input_fields - known_fields

        if unknown:
            raise serializers.ValidationError({
                'non_field_errors': [f"Unknown fields: {', '.join(unknown)}"]
            })


class ContextMixin:
    """
    Mixin for context-aware serializers.

    Provides easy access to request, user, and other context.

    Example:
        class MySerializer(ContextMixin, BaseSerializer):
            def validate_owner(self, value):
                if value != self.current_user:
                    raise ValidationError("Not your resource")
                return value
    """

    @property
    def request(self):
        """Get request from context."""
        return self.context.get('request')

    @property
    def current_user(self):
        """Get current user from context."""
        request = self.request
        if request and hasattr(request, 'user'):
            return request.user
        return None

    @property
    def tenant_id(self):
        """Get tenant ID from context."""
        return self.context.get('tenant_id')

    @property
    def view(self):
        """Get view from context."""
        return self.context.get('view')

    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get arbitrary value from context."""
        return self.context.get(key, default)


class DynamicFieldsMixin:
    """
    Mixin for request-based dynamic field selection.

    Supports ?fields=field1,field2 query parameter.

    Example:
        # GET /api/items/?fields=id,name
        class MySerializer(DynamicFieldsMixin, BaseModelSerializer):
            class Meta:
                model = MyModel
                fields = '__all__'
    """

    def __init__(self, *args, **kwargs):
        # Remove fields from kwargs if passed
        fields = kwargs.pop('fields', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop fields not in the specified list
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        else:
            # Check request for ?fields parameter
            request = self.context.get('request')
            if request:
                fields_param = request.query_params.get('fields')
                if fields_param:
                    allowed = set(fields_param.split(','))
                    existing = set(self.fields.keys())
                    for field_name in existing - allowed:
                        self.fields.pop(field_name)


class ExpandableMixin:
    """
    Mixin for expanding nested relations on request.

    Supports ?expand=relation1,relation2 query parameter.

    Class Attributes:
        expandable_fields: Dict of field_name -> SerializerClass

    Example:
        class OrderSerializer(ExpandableMixin, BaseModelSerializer):
            expandable_fields = {
                'customer': CustomerSerializer,
                'items': OrderItemSerializer,
            }

        # GET /api/orders/1/?expand=customer,items
    """

    expandable_fields = {}

    def __init__(self, *args, **kwargs):
        expand = kwargs.pop('expand', None)

        super().__init__(*args, **kwargs)

        if expand is None:
            request = self.context.get('request')
            if request:
                expand_param = request.query_params.get('expand')
                if expand_param:
                    expand = expand_param.split(',')

        if expand:
            for field_name in expand:
                if field_name in self.expandable_fields:
                    self.fields[field_name] = self.expandable_fields[field_name](
                        context=self.context
                    )


class PaginationMixin:
    """
    Mixin adding pagination fields to serializer.

    Example:
        class MyListSerializer(PaginationMixin, BaseSerializer):
            items = MyItemSerializer(many=True)
    """

    page = serializers.IntegerField(read_only=True, required=False)
    page_size = serializers.IntegerField(read_only=True, required=False)
    total_count = serializers.IntegerField(read_only=True, required=False)
    total_pages = serializers.IntegerField(read_only=True, required=False)
    has_next = serializers.BooleanField(read_only=True, required=False)
    has_previous = serializers.BooleanField(read_only=True, required=False)


class CacheMixin:
    """
    Mixin for response caching support.

    Example:
        class MySerializer(CacheMixin, BaseModelSerializer):
            cache_timeout = 300  # 5 minutes
    """

    cache_timeout = 300
    cache_key_prefix = ''

    def get_cache_key(self, instance) -> str:
        """Generate cache key for instance."""
        prefix = self.cache_key_prefix or self.__class__.__name__
        return f"{prefix}:{instance.pk}"


# =============================================================================
# BASE SERIALIZERS
# =============================================================================


class BaseSerializer(ValidationMixin, ContextMixin, serializers.Serializer):
    """
    Abstract base serializer with common functionality.

    Provides context awareness, validation hooks, and error handling.

    Class Attributes:
        error_messages: Custom error messages
        strict_validation: If True, reject unknown fields

    Override Points:
        - validate(): Add custom validation
        - validate_<field>(): Field-specific validation
        - to_representation(): Customize output
        - to_internal_value(): Customize input parsing

    Example:
        class MySerializer(BaseSerializer):
            name = serializers.CharField(max_length=200)
            email = serializers.EmailField()

            def validate_name(self, value):
                if value.lower() == 'admin':
                    raise serializers.ValidationError("Reserved name")
                return value
    """

    pass


class BaseModelSerializer(
    ValidationMixin,
    ContextMixin,
    DynamicFieldsMixin,
    serializers.ModelSerializer
):
    """
    Abstract base model serializer with common functionality.

    Provides all base serializer features plus model handling.

    Class Attributes:
        exclude_fields: Fields to always exclude
        readonly_fields: Fields to always be read-only
        auto_include_timestamps: If True, include created_at/updated_at

    Override Points:
        - get_field_names(): Customize included fields
        - create(): Customize creation logic
        - update(): Customize update logic

    Example:
        class MyModelSerializer(BaseModelSerializer):
            class Meta:
                model = MyModel
                fields = '__all__'
                exclude_fields = ['internal_notes']
    """

    exclude_fields = []
    readonly_fields = []
    auto_include_timestamps = True

    def get_field_names(self, declared_fields, info) -> List[str]:
        """Get field names with exclusions."""
        fields = super().get_field_names(declared_fields, info)

        if self.exclude_fields:
            fields = [f for f in fields if f not in self.exclude_fields]

        return fields

    def get_fields(self) -> Dict[str, serializers.Field]:
        """Get fields with readonly settings."""
        fields = super().get_fields()

        for field_name in self.readonly_fields:
            if field_name in fields:
                fields[field_name].read_only = True

        return fields


class TenantScopedSerializer(BaseModelSerializer):
    """
    Model serializer with automatic tenant handling.

    Automatically injects tenant_id on create.

    Class Attributes:
        tenant_field: Name of tenant field (default: 'tenant_id')
        auto_set_tenant: If True, auto-set from context

    Example:
        class MyTenantSerializer(TenantScopedSerializer):
            class Meta:
                model = MyTenantModel
                fields = '__all__'
    """

    tenant_field = 'tenant_id'
    auto_set_tenant = True

    def create(self, validated_data):
        """Create with automatic tenant setting."""
        if self.auto_set_tenant and self.tenant_id:
            validated_data[self.tenant_field] = self.tenant_id

        return super().create(validated_data)

    def validate(self, attrs):
        """Validate tenant access."""
        attrs = super().validate(attrs)

        # Prevent changing tenant_id on update
        if self.instance and self.tenant_field in attrs:
            if attrs[self.tenant_field] != getattr(self.instance, self.tenant_field):
                raise serializers.ValidationError({
                    self.tenant_field: "Cannot change tenant"
                })

        return attrs


class AuditableSerializer(BaseModelSerializer):
    """
    Model serializer with automatic audit field handling.

    Auto-sets created_by/modified_by from request user.

    Class Attributes:
        created_by_field: Name of created_by field
        modified_by_field: Name of modified_by field
        auto_set_audit: If True, auto-set audit fields

    Example:
        class MyAuditableSerializer(AuditableSerializer):
            class Meta:
                model = MyAuditableModel
                fields = '__all__'
    """

    created_by_field = 'created_by'
    modified_by_field = 'modified_by'
    auto_set_audit = True

    def create(self, validated_data):
        """Create with automatic audit user setting."""
        if self.auto_set_audit and self.current_user:
            username = getattr(self.current_user, 'username', str(self.current_user))
            validated_data[self.created_by_field] = username
            validated_data[self.modified_by_field] = username

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update with automatic audit user setting."""
        if self.auto_set_audit and self.current_user:
            username = getattr(self.current_user, 'username', str(self.current_user))
            validated_data[self.modified_by_field] = username

        return super().update(instance, validated_data)


class NestedWritableSerializer(BaseModelSerializer):
    """
    Model serializer with nested create/update support.

    Handles nested objects automatically on create and update.

    Class Attributes:
        nested_fields: Dict of field_name -> {'serializer': class, 'many': bool}

    Example:
        class OrderSerializer(NestedWritableSerializer):
            items = OrderItemSerializer(many=True)

            nested_fields = {
                'items': {'serializer': OrderItemSerializer, 'many': True}
            }

            class Meta:
                model = Order
                fields = '__all__'
    """

    nested_fields = {}

    def create(self, validated_data):
        """Create with nested objects."""
        nested_data = {}

        for field_name, config in self.nested_fields.items():
            if field_name in validated_data:
                nested_data[field_name] = validated_data.pop(field_name)

        instance = super().create(validated_data)

        for field_name, data in nested_data.items():
            config = self.nested_fields[field_name]
            if config.get('many'):
                for item_data in data:
                    item_data[self._get_parent_field()] = instance
                    self._create_nested(field_name, item_data)
            else:
                data[self._get_parent_field()] = instance
                self._create_nested(field_name, data)

        return instance

    def _get_parent_field(self) -> str:
        """Get the parent field name for nested objects."""
        return self.Meta.model._meta.model_name

    def _create_nested(self, field_name: str, data: Dict) -> Any:
        """Create a nested object."""
        config = self.nested_fields[field_name]
        serializer_class = config['serializer']
        serializer = serializer_class(data=data, context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class ReadOnlySerializer(ContextMixin, serializers.Serializer):
    """
    Base serializer for read-only use cases.

    All fields are automatically read-only.

    Example:
        class StatsSerializer(ReadOnlySerializer):
            total_count = serializers.IntegerField()
            avg_value = serializers.FloatField()
    """

    def get_fields(self) -> Dict[str, serializers.Field]:
        """Make all fields read-only."""
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Mixins
    'ValidationMixin',
    'ContextMixin',
    'DynamicFieldsMixin',
    'ExpandableMixin',
    'PaginationMixin',
    'CacheMixin',
    # Base Serializers
    'BaseSerializer',
    'BaseModelSerializer',
    'TenantScopedSerializer',
    'AuditableSerializer',
    'NestedWritableSerializer',
    'ReadOnlySerializer',
    # Utilities
    'get_serializer_setting',
]

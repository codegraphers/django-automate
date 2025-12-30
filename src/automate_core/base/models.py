"""
Django Automate - Abstract Base Models.

Provides abstract base classes for all models in the Django Automate ecosystem.
These bases ensure consistency, reusability, and extensibility across all models.

Usage:
    from automate_core.base.models import TimeStampedModel, TenantScopedModel

    class MyModel(TimeStampedModel):
        name = models.CharField(max_length=200)

Configuration:
    All base classes support configuration via class attributes that can be
    overridden in subclasses or via Django settings.

Design Principles:
    - DRY: Common fields and methods defined once
    - Extensibility: All methods can be overridden
    - Configurability: Settings-driven behavior
    - Composability: Mixins can be combined freely
"""

import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


def get_model_setting(key: str, default: Any = None) -> Any:
    """Get a model setting from Django settings."""
    model_settings = getattr(settings, 'AUTOMATE_MODELS', {})
    return model_settings.get(key, default)


# =============================================================================
# MANAGERS
# =============================================================================


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted records by default."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def deleted(self):
        return super().get_queryset().filter(is_deleted=True)

    def with_deleted(self):
        return super().get_queryset()


class TenantManager(models.Manager):
    """Manager that filters records by tenant."""

    def for_tenant(self, tenant_id):
        return self.get_queryset().filter(tenant_id=tenant_id)


class OrderedManager(models.Manager):
    """Manager for ordered models with position tracking."""

    def get_queryset(self):
        return super().get_queryset().order_by('position')


class StatusManager(models.Manager):
    """Manager for status-based filtering."""

    def by_status(self, status: str):
        return self.get_queryset().filter(status=status)

    def active(self):
        return self.get_queryset().exclude(status__in=['deleted', 'archived', 'disabled'])


# =============================================================================
# ABSTRACT BASE MODELS
# =============================================================================


class TimeStampedModel(models.Model):
    """Abstract base model with automatic timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TenantScopedModel(TimeStampedModel):
    """Abstract base model for multi-tenant isolation."""

    tenant_id = models.CharField(max_length=100, db_index=True)
    tenant_field = 'tenant_id'

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    @classmethod
    def get_current_tenant(cls) -> str | None:
        return None


class AuditableModel(TimeStampedModel):
    """Abstract base model with audit trail support."""

    created_by = models.CharField(max_length=150, blank=True, default='')
    modified_by = models.CharField(max_length=150, blank=True, default='')

    class Meta:
        abstract = True

    @classmethod
    def get_current_user(cls) -> str | None:
        return None


class SoftDeleteModel(TimeStampedModel):
    """Abstract base model with soft deletion support."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=150, blank=True, default='')

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = ''
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class OrderedModel(TimeStampedModel):
    """Abstract base model with ordering support."""

    position = models.PositiveIntegerField(default=0, db_index=True)
    objects = OrderedManager()

    class Meta:
        abstract = True
        ordering = ['position']


class SluggedModel(TimeStampedModel):
    """Abstract base model with auto-generated slug."""

    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    slug_source_field = 'name'

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def generate_unique_slug(self) -> str:
        from django.utils.text import slugify
        source = getattr(self, self.slug_source_field, '')
        slug = slugify(source)[:100]
        original_slug = slug
        counter = 1
        model_class = self.__class__
        while model_class.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix = f"-{counter}"
            slug = f"{original_slug[:100 - len(suffix)]}{suffix}"
            counter += 1
        return slug


class StatusModel(TimeStampedModel):
    """Abstract base model with status/state machine support."""

    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')]
    INITIAL_STATUS = 'active'

    status = models.CharField(max_length=50, db_index=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)

    objects = StatusManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.status:
            self.status = self.INITIAL_STATUS


class MetadataModel(TimeStampedModel):
    """Abstract base model with JSON metadata field."""

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True

    def get_meta(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.metadata
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set_meta(self, key: str, value: Any) -> None:
        keys = key.split('.')
        data = self.metadata
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value


# =============================================================================
# MIXINS
# =============================================================================


class HistoryMixin:
    """Mixin for tracking model history."""

    def get_history(self):
        if hasattr(self, 'history'):
            return self.history.all()
        return []


class CacheableMixin:
    """Mixin for cache support."""
    cache_timeout = 300

    @classmethod
    def get_cache_key(cls, **kwargs) -> str:
        key_parts = [f"{k}={v}" for k, v in sorted(kwargs.items())]
        return f"{cls.__name__.lower()}:{':'.join(key_parts)}"


class ValidatableMixin:
    """Mixin for enhanced validation."""

    def validate_fields(self) -> dict[str, str]:
        return {}


class SignalMixin:
    """Mixin for signal hooks."""

    def pre_save_hook(self):
        pass

    def post_save_hook(self, created: bool):
        pass


__all__ = [
    'SoftDeleteManager', 'TenantManager', 'OrderedManager', 'StatusManager',
    'TimeStampedModel', 'UUIDModel', 'TenantScopedModel', 'AuditableModel',
    'SoftDeleteModel', 'OrderedModel', 'SluggedModel', 'StatusModel', 'MetadataModel',
    'HistoryMixin', 'CacheableMixin', 'ValidatableMixin', 'SignalMixin',
    'get_model_setting',
]

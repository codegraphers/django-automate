"""
Base classes and mixins for Django Automate API.

This module provides abstract base classes that enable:
- Configurability via Django settings
- Reusable mixins for common functionality
- Extensible base ViewSets for customization

Usage:
    from automate_api.v1.base import BaseViewSet, CORSMixin

    class MyViewSet(BaseViewSet):
        # Inherit all base configuration
        pass

    class MyAPIView(CORSMixin, APIView):
        # Add CORS support to any view
        pass

Configuration:
    Override defaults in Django settings:

    AUTOMATE_API = {
        'DEFAULT_THROTTLE_RATES': {
            'tenant': '120/min',
            'token': '60/min',
        },
        'CORS_ALLOWED_ORIGINS': ['*'],
        'PAGINATION_PAGE_SIZE': 50,
    }
"""

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import BearerTokenAuthentication
from .pagination import CursorPagination
from .permissions import IsAuthenticatedAndTenantScoped
from .throttling import TenantRateThrottle, TokenRateThrottle


def get_api_setting(key: str, default=None):
    """
    Retrieve API setting from Django settings.

    Looks for AUTOMATE_API dict in settings, falls back to default.

    Args:
        key: Setting key to retrieve
        default: Default value if not found

    Returns:
        Setting value or default

    Example:
        >>> get_api_setting('PAGINATION_PAGE_SIZE', 50)
        50
    """
    api_settings = getattr(settings, 'AUTOMATE_API', {})
    return api_settings.get(key, default)


class ConfigurableMixin:
    """
    Mixin providing runtime configuration via Django settings.

    All attributes with 'setting_' prefix are resolved from Django settings
    at runtime, allowing configuration without code changes.

    Class Attributes:
        setting_key_prefix: Prefix for settings lookup (default: 'AUTOMATE_API')

    Example:
        class MyViewSet(ConfigurableMixin, ViewSet):
            # Will look up AUTOMATE_API['MY_SETTING'] or use 'default'
            my_setting = 'default'

            def get_my_setting(self):
                return get_api_setting('MY_SETTING', self.my_setting)
    """

    setting_key_prefix = 'AUTOMATE_API'

    @classmethod
    def get_setting(cls, key: str, default=None):
        """Get a setting value, checking Django settings first."""
        return get_api_setting(key, default)


class CORSMixin:
    """
    Mixin providing CORS header support for API views.

    Automatically adds CORS headers to all responses, with configurable
    allowed origins, methods, and headers.

    Class Attributes:
        cors_allowed_origins: List of allowed origins (default: ['*'])
        cors_allowed_methods: List of allowed methods (default: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        cors_allowed_headers: List of allowed headers

    Configuration via settings:
        AUTOMATE_API = {
            'CORS_ALLOWED_ORIGINS': ['https://example.com'],
            'CORS_ALLOWED_METHODS': ['GET', 'POST'],
        }

    Example:
        class MyAPIView(CORSMixin, APIView):
            cors_allowed_origins = ['https://mysite.com']
    """

    cors_allowed_origins = ['*']
    cors_allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    cors_allowed_headers = ['Content-Type', 'Authorization', 'X-Embed-Key', 'X-Session-Id', 'X-API-Key']
    cors_expose_headers = []
    cors_max_age = 86400  # 24 hours

    def get_cors_allowed_origins(self):
        """Get allowed origins, checking settings first."""
        return get_api_setting('CORS_ALLOWED_ORIGINS', self.cors_allowed_origins)

    def get_cors_allowed_methods(self):
        """Get allowed methods, checking settings first."""
        return get_api_setting('CORS_ALLOWED_METHODS', self.cors_allowed_methods)

    def get_cors_allowed_headers(self):
        """Get allowed headers, checking settings first."""
        return get_api_setting('CORS_ALLOWED_HEADERS', self.cors_allowed_headers)

    def add_cors_headers(self, response):
        """Add CORS headers to a response."""
        origins = self.get_cors_allowed_origins()
        origin_header = ', '.join(origins) if isinstance(origins, list) else origins

        response['Access-Control-Allow-Origin'] = origin_header
        response['Access-Control-Allow-Methods'] = ', '.join(self.get_cors_allowed_methods())
        response['Access-Control-Allow-Headers'] = ', '.join(self.get_cors_allowed_headers())

        if self.cors_expose_headers:
            response['Access-Control-Expose-Headers'] = ', '.join(self.cors_expose_headers)

        response['Access-Control-Max-Age'] = str(self.cors_max_age)
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        """Override to add CORS headers to all responses."""
        response = super().finalize_response(request, response, *args, **kwargs)
        return self.add_cors_headers(response)

    def options(self, request, *args, **kwargs):
        """Handle CORS preflight requests."""
        response = Response(status=status.HTTP_200_OK)
        return self.add_cors_headers(response)


class TenantFilterMixin:
    """
    Mixin that filters querysets by tenant from request principal.

    Automatically applies tenant filtering to querysets based on the
    authenticated principal's tenant_id.

    Example:
        class MyViewSet(TenantFilterMixin, ModelViewSet):
            queryset = MyModel.objects.all()
            # Queryset automatically filtered by tenant_id
    """

    tenant_field = 'tenant_id'

    def get_queryset(self):
        """Filter queryset by tenant from request principal."""
        qs = super().get_queryset()
        principal = getattr(self.request, 'principal', None)
        if principal and hasattr(principal, 'tenant_id'):
            filter_kwargs = {self.tenant_field: principal.tenant_id}
            qs = qs.filter(**filter_kwargs)
        return qs


class RateLimitMixin:
    """
    Mixin providing configurable rate limiting.

    Class Attributes:
        rate_limit_key_prefix: Cache key prefix for rate limiting
        rate_limit_per_minute: Requests allowed per minute (default: 60)

    Configuration via settings:
        AUTOMATE_API = {
            'RATE_LIMIT_PER_MINUTE': 120,
        }
    """

    rate_limit_key_prefix = 'api_rate'
    rate_limit_per_minute = 60

    def get_rate_limit(self):
        """Get rate limit, checking settings first."""
        return get_api_setting('RATE_LIMIT_PER_MINUTE', self.rate_limit_per_minute)

    def check_rate_limit(self, key: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            key: Unique key for rate limiting (e.g., user_id, ip)

        Returns:
            True if allowed, False if rate limited
        """
        from django.core.cache import cache

        cache_key = f"{self.rate_limit_key_prefix}:{key}"
        count = cache.get(cache_key, 0)

        if count >= self.get_rate_limit():
            return False

        cache.set(cache_key, count + 1, 60)  # 60 second window
        return True


class BaseAPIView(ConfigurableMixin, APIView):
    """
    Abstract base class for all API views.

    Provides:
    - Configurable authentication
    - Configurable permissions
    - Configurable throttling
    - Tenant filtering support

    Class Attributes:
        authentication_classes: List of authentication classes
        permission_classes: List of permission classes
        throttle_classes: List of throttle classes

    Override these in subclasses or via Django settings.

    Example:
        class MyView(BaseAPIView):
            permission_classes = [IsAdminUser]

            def get(self, request):
                return Response({'status': 'ok'})
    """

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    throttle_classes = [TenantRateThrottle, TokenRateThrottle]


class BaseViewSet(ConfigurableMixin, TenantFilterMixin, viewsets.ViewSet):
    """
    Abstract base class for all ViewSets.

    Provides:
    - Configurable authentication, permissions, throttling
    - Automatic tenant filtering
    - Pagination support

    Class Attributes:
        authentication_classes: Authentication backends
        permission_classes: Permission checks
        throttle_classes: Rate limiting
        pagination_class: Pagination handler

    Example:
        class MyViewSet(BaseViewSet):
            def list(self, request):
                return Response([])
    """

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    throttle_classes = [TenantRateThrottle, TokenRateThrottle]
    pagination_class = CursorPagination


class BaseModelViewSet(ConfigurableMixin, TenantFilterMixin, viewsets.ModelViewSet):
    """
    Abstract base class for Model ViewSets.

    Provides all BaseViewSet features plus:
    - Automatic CRUD operations
    - Queryset and serializer configuration

    Example:
        class MyModelViewSet(BaseModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
    """

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    throttle_classes = [TenantRateThrottle, TokenRateThrottle]
    pagination_class = CursorPagination


class BaseReadOnlyViewSet(ConfigurableMixin, TenantFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    Abstract base class for read-only ViewSets.

    Use for resources that should not be modified via API.

    Example:
        class AuditLogViewSet(BaseReadOnlyViewSet):
            queryset = AuditLog.objects.all()
            serializer_class = AuditLogSerializer
    """

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    throttle_classes = [TenantRateThrottle, TokenRateThrottle]
    pagination_class = CursorPagination


class StaffOnlyMixin:
    """
    Mixin that restricts access to staff members only.

    Use for admin-only endpoints.

    Example:
        class AdminViewSet(StaffOnlyMixin, BaseViewSet):
            pass
    """

    def check_permissions(self, request):
        """Check that user is staff."""
        super().check_permissions(request)
        if not request.user or not request.user.is_staff:
            self.permission_denied(request, message="Staff access required")


class PublicAPIMixin:
    """
    Mixin for public API endpoints (no authentication required).

    Use sparingly - only for truly public endpoints.

    Example:
        class HealthCheckView(PublicAPIMixin, BaseAPIView):
            def get(self, request):
                return Response({'status': 'healthy'})
    """

    authentication_classes = []
    permission_classes = []

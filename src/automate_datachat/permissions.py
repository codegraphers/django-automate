"""
DataChat Permissions.

Custom permission classes for DataChat API endpoints.

All permissions are designed to be:
- Overridable via inheritance
- Configurable via class attributes
- Composable with other permissions
"""

import fnmatch
from urllib.parse import urlparse

from rest_framework import permissions


class IsStaffMember(permissions.BasePermission):
    """
    Permission that allows access only to staff members.

    Used for admin chat endpoints.

    Example:
        class MyView(APIView):
            permission_classes = [IsStaffMember]
    """

    message = "Staff access required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class EmbedAPIKeyPermission(permissions.BasePermission):
    """
    Permission that validates embed API key.

    Checks X-Embed-Key header or 'key' query parameter against
    the embed's configured api_key.

    Class Attributes:
        header_name: HTTP header to check (default: 'X-Embed-Key')
        query_param: Query parameter to check (default: 'key')

    Example:
        class EmbedChatView(APIView):
            permission_classes = [EmbedAPIKeyPermission]
    """

    message = "Invalid API key."
    header_name = 'X-Embed-Key'
    query_param = 'key'

    def has_permission(self, request, view):
        # Embed must be set by view
        embed = getattr(view, 'embed', None)
        if not embed:
            return False

        key = (
            request.headers.get(self.header_name) or
            request.query_params.get(self.query_param)
        )
        return key == embed.api_key


class EmbedOriginPermission(permissions.BasePermission):
    """
    Permission that validates request origin against embed's allowed domains.

    Checks Origin or Referer header against the embed's allowed_domains list.
    Supports wildcards and pattern matching.

    Class Attributes:
        allow_null_origin: Whether to allow 'null' origins (file:// URLs)

    Example:
        class EmbedChatView(APIView):
            permission_classes = [EmbedOriginPermission]
    """

    message = "Origin not allowed."
    allow_null_origin = False

    def has_permission(self, request, view):
        embed = getattr(view, 'embed', None)
        if not embed or not embed.allowed_domains:
            return True  # No restrictions

        origin = request.headers.get('Origin') or request.headers.get('Referer', '')

        if not origin:
            return False

        # Handle null origin (file:// URLs)
        if origin == 'null':
            if self.allow_null_origin:
                return 'null' in embed.allowed_domains or '*' in embed.allowed_domains
            return False

        # Parse origin
        parsed = urlparse(origin)
        netloc = parsed.netloc
        host = netloc.split(':')[0]

        for pattern in embed.allowed_domains:
            if pattern == '*':
                return True
            if fnmatch.fnmatch(origin, pattern):
                return True
            if fnmatch.fnmatch(netloc, pattern):
                return True
            if fnmatch.fnmatch(host, pattern):
                return True

        return False


class EmbedRateLimitPermission(permissions.BasePermission):
    """
    Permission that enforces rate limiting per embed per session.

    Uses Django cache to track request counts.

    Class Attributes:
        cache_key_prefix: Prefix for cache keys
        window_seconds: Rate limit window in seconds (default: 60)
    """

    message = "Rate limit exceeded."
    cache_key_prefix = 'embed_rate'
    window_seconds = 60

    def has_permission(self, request, view):
        from django.core.cache import cache

        embed = getattr(view, 'embed', None)
        if not embed:
            return False

        session_key = (
            request.headers.get('X-Session-Id') or
            request.META.get('REMOTE_ADDR', 'unknown')
        )

        cache_key = f"{self.cache_key_prefix}:{embed.id}:{session_key}"
        count = cache.get(cache_key, 0)

        if count >= embed.rate_limit_per_minute:
            return False

        cache.set(cache_key, count + 1, self.window_seconds)
        return True

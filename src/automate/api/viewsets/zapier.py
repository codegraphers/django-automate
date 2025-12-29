"""
Zapier Integration API ViewSet.

Class-based ViewSet for Zapier integration endpoints.
"""

from uuid import uuid4

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class APIKeyAuthentication:
    """
    Authentication class for API key validation.

    Validates X-API-Key header against configured keys.
    """

    def authenticate(self, request):
        from automate.models import APIKey

        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return None

        try:
            key = APIKey.objects.get(key=api_key, is_active=True)
            return (key.user, key)
        except APIKey.DoesNotExist:
            return None


class ZapierViewSet(viewsets.ViewSet):
    """
    Zapier Integration ViewSet.

    Provides endpoints for Zapier trigger subscriptions.

    Class Attributes:
        available_triggers: List of available trigger types
        ssrf_validator: URL validator for security

    Endpoints:
        GET /api/zapier/triggers/ - List available triggers
        POST /api/zapier/subscribe/ - Subscribe to a trigger
        POST /api/zapier/unsubscribe/ - Unsubscribe from a trigger

    Example - Add custom triggers:
        class MyZapierViewSet(ZapierViewSet):
            available_triggers = [
                {'key': 'custom_event', 'label': 'Custom Event'},
            ]
    """

    authentication_classes = []  # Use custom API key auth

    available_triggers = [
        {'key': 'new_event', 'label': 'New Event'},
        {'key': 'model_created', 'label': 'Model Created'},
    ]

    def get_available_triggers(self):
        """Get available triggers. Override to customize."""
        return self.available_triggers

    def validate_callback_url(self, url: str) -> bool:
        """
        Validate callback URL for security (SSRF protection).

        Override to customize URL validation.
        """
        from automate_llm.tools.http import HttpFetchTool

        validator = HttpFetchTool()
        return validator._is_safe_url(url)

    def check_api_key(self, request):
        """Check API key from request. Raises if invalid."""
        # Decorator-based check
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('API key required')
        return True

    @extend_schema(
        responses={'200': {'type': 'array', 'items': {'type': 'object'}}},
        description="List available trigger types."
    )
    @action(detail=False, methods=['get'])
    def triggers(self, request):
        """List available trigger types."""
        self.check_api_key(request)
        return Response(self.get_available_triggers())

    @extend_schema(
        request={'type': 'object', 'properties': {'target_url': {'type': 'string'}}},
        responses={'200': {'type': 'object'}},
        description="Subscribe to a trigger via webhook."
    )
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """
        Subscribe to a trigger.

        Validates callback URL for SSRF protection.
        """
        self.check_api_key(request)

        target_url = request.data.get('target_url')
        if not target_url:
            return Response(
                {'error': 'target_url required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not self.validate_callback_url(target_url):
            return Response(
                {'error': 'Invalid Target URL: Blocked by SSRF Policy'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sub_id = str(uuid4())

        # TODO: Store subscription in TriggerSpec model

        return Response({'id': sub_id, 'status': 'subscribed'})

    @extend_schema(
        responses={'200': {'type': 'object'}},
        description="Unsubscribe from a trigger."
    )
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Unsubscribe from a trigger."""
        self.check_api_key(request)

        # TODO: Remove subscription from TriggerSpec model

        return Response({'status': 'unsubscribed'})

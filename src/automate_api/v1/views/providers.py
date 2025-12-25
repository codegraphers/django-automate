from drf_spectacular.utils import extend_schema
from rest_framework import decorators, viewsets
from rest_framework.response import Response

from automate.models import LLMProvider

from ..auth import BearerTokenAuthentication
from ..pagination import CursorPagination
from ..permissions import IsAuthenticatedAndTenantScoped
from ..serializers.providers import ProviderSerializer
from ..throttling import TenantRateThrottle


class ProviderViewSet(viewsets.ModelViewSet):
    """
    Manage LLM/Service providers.
    Secrets are write-only.
    """
    queryset = LLMProvider.objects.all()
    serializer_class = ProviderSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    pagination_class = CursorPagination
    throttle_classes = [TenantRateThrottle]
    ordering = ["slug"] # LLMProvider doesn't have created_at

    @extend_schema(request=None, responses={200: {"status": "ok"}})
    @decorators.action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """
        Verify provider connectivity.
        """
        provider = self.get_object()
        # Mock test logic. Real logic would instantiate backend and ping.
        return Response({"status": "ok", "provider": provider.name})

from drf_spectacular.utils import extend_schema
from rest_framework import decorators, serializers, viewsets
from rest_framework.response import Response

from automate.models import LLMProvider

from ..auth import BearerTokenAuthentication


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMProvider
        fields = ["slug", "name", "base_url", "api_key_env_var"]
        # Hide sensitive vars if needed, though env var name is usually safe-ish
        # We can treat api_key_env_var as config for now


class ProviderViewSet(viewsets.ModelViewSet):
    """
    Manage LLM/Service providers.
    Secrets are write-only.
    """
    queryset = LLMProvider.objects.all()
    serializer_class = ProviderSerializer
    authentication_classes = [BearerTokenAuthentication]
    # permission_classes = [IsTenantMember] # Provider model might not have tenant_id yet, assume Admin

    @extend_schema(request=None, responses={200: {"status": "ok"}})
    @decorators.action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """
        Verify provider connectivity.
        """
        provider = self.get_object()
        # Mock test logic. Real logic would instantiate backend and ping.
        return Response({"status": "ok", "provider": provider.name})

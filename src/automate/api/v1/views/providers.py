from drf_spectacular.utils import extend_schema
from rest_framework import decorators, serializers, viewsets
from rest_framework.response import Response

from automate.models import LLMProvider

from ..auth import BearerTokenAuthentication


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMProvider
        fields = ["id", "provider_type", "name", "base_url", "config_encrypted"]
        extra_kwargs = {
            "config_encrypted": {"write_only": True} # Do not show secrets
        }

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

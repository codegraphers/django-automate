from drf_spectacular.utils import extend_schema
from rest_framework import decorators, mixins, viewsets
from rest_framework.response import Response

from automate_core.models import Artifact

from ..auth import BearerTokenAuthentication
from ..pagination import CursorPagination
from ..permissions import IsAuthenticatedAndTenantScoped
from ..serializers.artifacts import ArtifactSerializer
from ..throttling import TenantRateThrottle


class ArtifactViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Artifact.objects.all().order_by("-created_at")
    serializer_class = ArtifactSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    pagination_class = CursorPagination
    throttle_classes = [TenantRateThrottle]

    def get_queryset(self):
        qs = super().get_queryset()
        principal = getattr(self.request, "principal", None)
        if principal:
            qs = qs.filter(tenant_id=principal.tenant_id)
        return qs

    @extend_schema(summary="Download artifact content")
    @decorators.action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        artifact = self.get_object()
        # Mock presigned URL
        download_url = f"https://s3.example.com/artifacts/{artifact.id}"
        return Response({"url": download_url})

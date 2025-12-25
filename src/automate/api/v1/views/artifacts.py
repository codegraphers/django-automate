from drf_spectacular.utils import extend_schema
from rest_framework import decorators, mixins, serializers, viewsets
from rest_framework.response import Response

from automate_core.models import Artifact

from ..auth import BearerTokenAuthentication
from ..permissions import IsTenantMember


class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = ["id", "tenant_id", "uri", "kind", "size_bytes", "created_at"]
        read_only_fields = fields

class ArtifactViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Artifact.objects.all().order_by("-created_at")
    serializer_class = ArtifactSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsTenantMember]

    @extend_schema(summary="Download artifact content")
    @decorators.action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Get secure download URL (S3 presigned) or stream content.
        """
        artifact = self.get_object()

        # In a real impl, this would generate a presigned S3 URL
        # download_url = s3_client.generate_presigned_url(...)
        download_url = f"https://s3.example.com/artifacts/{artifact.id}"

        # Or stream if local
        return Response({"url": download_url})

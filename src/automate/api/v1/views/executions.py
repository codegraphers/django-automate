from rest_framework import mixins, serializers, viewsets

from automate_core.models import Execution

from ..auth import BearerTokenAuthentication
from ..permissions import IsTenantMember


class ExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Execution
        fields = [
            "id", "tenant_id", "automation", "workflow_version",
            "status", "created_at", "updated_at", "result_data"
        ]
        read_only_fields = fields

class ExecutionViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Execution.objects.all().order_by("-created_at")
    serializer_class = ExecutionSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        # Filtering logic would go here
        return super().get_queryset()

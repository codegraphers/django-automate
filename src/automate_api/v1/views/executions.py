from rest_framework import mixins, viewsets

from automate_core.models import Execution

from ..auth import BearerTokenAuthentication
from ..pagination import CursorPagination
from ..permissions import IsAuthenticatedAndTenantScoped
from ..serializers.executions import ExecutionSerializer
from ..throttling import TenantRateThrottle, TokenRateThrottle


class ExecutionViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Execution.objects.all().order_by("-started_at")
    serializer_class = ExecutionSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    pagination_class = CursorPagination
    throttle_classes = [TenantRateThrottle, TokenRateThrottle]

    def get_queryset(self):
        qs = super().get_queryset()
        principal = getattr(self.request, "principal", None)
        if principal:
            qs = qs.filter(tenant_id=principal.tenant_id)
        return qs

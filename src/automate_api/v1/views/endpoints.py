from drf_spectacular.utils import extend_schema
from rest_framework import decorators, status, viewsets
from rest_framework.response import Response

from automate_core.jobs.models import Job, JobStatusChoices
from automate_core.models import Automation

from ..auth import BearerTokenAuthentication
from ..pagination import CursorPagination
from ..permissions import IsAuthenticatedAndTenantScoped
from ..serializers.endpoints import EndpointRunRequest, EndpointRunResponse, EndpointSerializer
from ..throttling import TenantRateThrottle, TokenRateThrottle


class EndpointViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Exposes Automations as callable Endpoints.
    """
    queryset = Automation.objects.filter(is_active=True)
    serializer_class = EndpointSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    pagination_class = CursorPagination
    throttle_classes = [TenantRateThrottle, TokenRateThrottle]

    def get_queryset(self):
        # Filter by tenant from Principal
        qs = super().get_queryset()
        principal = getattr(self.request, "principal", None)
        if principal:
            qs = qs.filter(tenant_id=principal.tenant_id)
        return qs

    @extend_schema(request=EndpointRunRequest, responses=EndpointRunResponse)
    @decorators.action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """
        Trigger an execution of this endpoint.
        """
        automation = self.get_object()

        serializer = EndpointRunRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data["payload"]

        # In a real impl, we'd look up the Trigger/Workflow and dispatch.
        # Here we just create a Job for the engine.

        job = Job.objects.create(
            topic="automation.run",
            payload_redacted=payload,
            status=JobStatusChoices.QUEUED,
            correlation_id=request.correlation_id,
            tenant_id=automation.tenant_id
        )

        return Response({"job_id": job.id}, status=status.HTTP_202_ACCEPTED)

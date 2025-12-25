
from drf_spectacular.utils import extend_schema
from rest_framework import decorators, mixins, serializers, status, viewsets
from rest_framework.response import Response

from automate_core.jobs.models import Job, JobStatusChoices

# Endpoints are conceptually 'Actions' or 'Workflows' exposed as callable units.
# For now, we'll map them to Automations or specific labeled triggers.
# Using a mock-ish implementation since Endpoint model isn't strictly defined in Core yet.
# We will treat Automations as Endpoints for this V1.
from automate_core.models import Automation

from ..auth import BearerTokenAuthentication
from ..permissions import IsTenantMember


class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Automation
        fields = ["id", "name", "description", "is_active"]

class EndpointRunRequest(serializers.Serializer):
    payload = serializers.DictField(default={})
    async_mode = serializers.BooleanField(default=True)

class EndpointViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    Exposes Automations as callable Endpoints.
    """
    queryset = Automation.objects.filter(is_active=True)
    serializer_class = EndpointSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsTenantMember]

    @extend_schema(request=EndpointRunRequest, responses={202: {"job_id": "uuid"}})
    @decorators.action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """
        Trigger an endpoint execution.
        Returns a Job ID.
        """
        automation = self.get_object()
        serializer = EndpointRunRequest(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = serializer.validated_data["payload"]

        # In a real impl, we'd look up the Trigger/Workflow and dispatch.
        # Here we just create a Job for the engine.

        # Create Job
        job = Job.objects.create(
            topic="automation.run",
            payload_redacted=payload,
            tenant_id=getattr(automation, "tenant_id", "default"),
            status=JobStatusChoices.QUEUED
        )

        # Enqueue (Mocking queue submission here, usually Service layer does this)
        # queue.submit(job.id)

        return Response({"job_id": job.id}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(summary="Stream endpoint execution")
    @decorators.action(detail=True, methods=["post"])
    def stream(self, request, pk=None):
        """
        Trigger and stream results immediately (SSE).
        Wraps run + job.events.
        """
        # Logic: Create job, then yield from job events immediately.
        # Re-uses logic from JobViewSet.events essentially.
        return Response({"message": "Not implemented yet"}, status=status.HTTP_501_NOT_IMPLEMENTED)

from drf_spectacular.utils import extend_schema
from rest_framework import status, views
from rest_framework.response import Response

from automate.ingestion import EventIngestionService

from ..auth import BearerTokenAuthentication
from ..permissions import IsAuthenticatedAndTenantScoped
from ..serializers.events import IngestEventResponse, IngestEventSerializer
from ..throttling import TenantRateThrottle


class EventIngestView(views.APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    throttle_classes = [TenantRateThrottle]

    @extend_schema(request=IngestEventSerializer, responses={201: IngestEventResponse})
    def post(self, request, *args, **kwargs):
        serializer = IngestEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        principal = getattr(request, "principal", None)
        tenant_id = principal.tenant_id if principal else "default"

        # Ingest
        service = EventIngestionService()
        result = service.ingest_event(
            tenant_id=tenant_id,
            event_type=data["event_type"],
            payload=data["payload"],
            idempotency_key=data.get("idempotency_key"),
            source=data["source"]
        )

        return Response(
            {
                "status": "accepted" if result.status == "queued" else "processed",
                "event_id": result.event_id,
                "action": result.status
            },
            status=status.HTTP_201_CREATED
        )

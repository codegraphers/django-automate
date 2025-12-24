from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, views
from rest_framework.response import Response

from automate.ingestion import EventIngestionService

from ..auth import BearerTokenAuthentication


class IngestEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    payload = serializers.DictField(default={})
    idempotency_key = serializers.CharField(required=False)
    source = serializers.CharField(default="api")

class EventIngestionView(views.APIView):
    authentication_classes = [BearerTokenAuthentication]
    # Scopes: events:write

    @extend_schema(request=IngestEventSerializer, responses={201: {"status": "accepted", "event_id": "uuid"}})
    def post(self, request, *args, **kwargs):
        serializer = IngestEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Ingest
        service = EventIngestionService()
        result = service.ingest_event(
            tenant_id=getattr(request.user, "tenant_id", "default"), # Fallback
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

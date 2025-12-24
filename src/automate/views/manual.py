from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from ..ingestion import EventIngestionService


class ManualTriggerSerializer(serializers.Serializer):
    event = serializers.CharField(help_text="Slug of the automation event (optional logic)", required=False)
    payload = serializers.DictField(help_text="JSON payload for the event")


class ManualTriggerView(APIView):
    """
    Ingests a manual event into the system.
    """

    serializer_class = ManualTriggerSerializer
    # authentication_classes = [ApiKeyAuthentication] # TODO: Port require_api_key logic to DRF Auth

    @extend_schema(
        request=ManualTriggerSerializer,
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}, "event_id": {"type": "string"}}}
        },
    )
    def post(self, request):
        serializer = ManualTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        payload = data.get("payload", {})

        event = EventIngestionService.ingest_event(
            event_type="manual", source="api", payload=payload, idempotency_key=None
        )

        return Response({"status": "ok", "event_id": str(event.id)})

from rest_framework import serializers


class IngestEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    payload = serializers.DictField(default={})
    idempotency_key = serializers.CharField(required=False)
    source = serializers.CharField(default="api")

class IngestEventResponse(serializers.Serializer):
    status = serializers.CharField()
    event_id = serializers.CharField()
    action = serializers.CharField()

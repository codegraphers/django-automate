from rest_framework import serializers


class ModalRunRequestSerializer(serializers.Serializer):
    task_type = serializers.CharField(required=True)
    input = serializers.DictField(required=True)
    params = serializers.DictField(required=False, default=dict)


class ModalArtifactSerializer(serializers.Serializer):
    kind = serializers.CharField()
    uri = serializers.CharField()
    mime = serializers.CharField()
    size_bytes = serializers.IntegerField()
    meta = serializers.DictField()


class ModalResultSerializer(serializers.Serializer):
    task_type = serializers.CharField()
    outputs = serializers.DictField()
    artifacts = serializers.ListField(child=ModalArtifactSerializer())
    usage = serializers.DictField()
    # We redact raw_provider_meta by default in API responses or include safe subset


class ModalJobSerializer(serializers.Serializer):
    job_id = serializers.CharField()
    status = serializers.CharField(source="state")
    created_at = serializers.DateTimeField()
    # Add other fields as needed

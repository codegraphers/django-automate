from rest_framework import serializers

from automate_core.models import Automation


class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Automation
        fields = ["id", "name", "description", "is_active"]

class EndpointRunRequest(serializers.Serializer):
    payload = serializers.DictField(default={})

class EndpointRunResponse(serializers.Serializer):
    job_id = serializers.CharField()

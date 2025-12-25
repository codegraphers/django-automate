from rest_framework import serializers

from automate_core.jobs.models import Job


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id", "kind", "topic", "status", "attempts",
            "max_attempts", "payload_redacted", "created_at", "updated_at"
        ]
        read_only_fields = fields

class CancelResponse(serializers.Serializer):
    job_id = serializers.CharField()
    canceled = serializers.BooleanField()

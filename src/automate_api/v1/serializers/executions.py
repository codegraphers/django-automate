from rest_framework import serializers

from automate_core.models import Execution


class ExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Execution
        fields = [
            "id", "tenant_id", "automation", "workflow_version",
            "status", "started_at", "finished_at", "context"
        ]
        read_only_fields = fields

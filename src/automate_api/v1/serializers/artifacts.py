from rest_framework import serializers

from automate_core.models import Artifact


class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = ["id", "tenant_id", "uri", "kind", "size_bytes", "created_at"]
        read_only_fields = fields

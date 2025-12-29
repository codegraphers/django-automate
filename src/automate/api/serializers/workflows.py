"""
Workflow API Serializers.

Provides validation and serialization for Workflow API endpoints.
"""

from rest_framework import serializers


class WorkflowNodeSerializer(serializers.Serializer):
    """Serializer for workflow graph nodes."""
    
    id = serializers.CharField()
    type = serializers.ChoiceField(choices=['trigger', 'action', 'condition', 'transform'])
    config = serializers.DictField(default=dict)
    position = serializers.DictField(required=False)


class WorkflowEdgeSerializer(serializers.Serializer):
    """Serializer for workflow graph edges."""
    
    source = serializers.CharField()
    target = serializers.CharField()
    condition = serializers.CharField(required=False, allow_blank=True)


class WorkflowGraphSerializer(serializers.Serializer):
    """Serializer for complete workflow graph."""
    
    nodes = WorkflowNodeSerializer(many=True)
    edges = WorkflowEdgeSerializer(many=True)


class WorkflowCreateRequestSerializer(serializers.Serializer):
    """
    Serializer for workflow creation requests.
    
    Example:
        {
            "name": "My Workflow",
            "graph": {
                "nodes": [...],
                "edges": [...]
            }
        }
    """
    
    name = serializers.CharField(
        max_length=200,
        default="Untitled Workflow",
        help_text="Human-readable name for the workflow"
    )
    graph = WorkflowGraphSerializer(
        help_text="Workflow graph with nodes and edges"
    )


class WorkflowCreateResponseSerializer(serializers.Serializer):
    """Serializer for workflow creation response."""
    
    id = serializers.UUIDField()
    slug = serializers.SlugField()
    workflow_version = serializers.IntegerField()
    message = serializers.CharField()


class WorkflowDetailSerializer(serializers.Serializer):
    """Serializer for workflow detail response."""
    
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    graph = serializers.DictField()


class WorkflowUpdateRequestSerializer(serializers.Serializer):
    """Serializer for workflow update requests."""
    
    name = serializers.CharField(max_length=200, required=False)
    graph = WorkflowGraphSerializer()


class WorkflowUpdateResponseSerializer(serializers.Serializer):
    """Serializer for workflow update response."""
    
    id = serializers.UUIDField()
    message = serializers.CharField()

"""
Workflow API ViewSets.

Class-based ViewSets for workflow CRUD operations.

All ViewSets are designed to be:
- Configurable via class attributes
- Overridable via inheritance
- Extensible with custom service classes

Example - Custom Workflow ViewSet:
    from automate.api.viewsets.workflows import WorkflowViewSet
    
    class MyWorkflowViewSet(WorkflowViewSet):
        # Use custom service
        service_class = MyWorkflowService
"""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from automate.models import Automation
from automate.services.workflow_service import WorkflowService, default_workflow_service

from .serializers.workflows import (
    WorkflowCreateRequestSerializer,
    WorkflowCreateResponseSerializer,
    WorkflowDetailSerializer,
    WorkflowUpdateRequestSerializer,
    WorkflowUpdateResponseSerializer,
)


class StaffOnlyMixin:
    """Mixin that restricts access to staff members."""
    
    def check_permissions(self, request):
        super().check_permissions(request)
        if not request.user or not request.user.is_staff:
            self.permission_denied(request, message="Staff access required")


class WorkflowViewSet(StaffOnlyMixin, viewsets.ViewSet):
    """
    Workflow API ViewSet.
    
    Provides CRUD operations for workflow management.
    
    Class Attributes:
        service_class: Service class for workflow operations
        queryset: Base queryset for automation lookup
        
    Endpoints:
        POST /api/workflows/ - Create workflow
        GET /api/workflows/{id}/ - Get workflow details
        PUT /api/workflows/{id}/ - Update workflow
        
    Example - Override service:
        class MyWorkflowViewSet(WorkflowViewSet):
            service_class = MyWorkflowService
    """
    
    service_class = WorkflowService
    queryset = Automation.objects.all()
    
    def get_service(self) -> WorkflowService:
        """Get workflow service instance. Override to customize."""
        return self.service_class()
    
    def get_object(self, pk):
        """Get automation by ID."""
        return get_object_or_404(self.queryset, id=pk)
    
    @extend_schema(
        request=WorkflowCreateRequestSerializer,
        responses={201: WorkflowCreateResponseSerializer},
        description="Create a new workflow with automation and trigger."
    )
    def create(self, request):
        """
        Create a new workflow.
        
        Creates automation, trigger, and initial workflow version.
        """
        serializer = WorkflowCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        automation, workflow = service.create_workflow(
            name=serializer.validated_data['name'],
            graph=serializer.validated_data['graph'],
            created_by=request.user.username
        )
        
        return Response({
            'id': str(automation.id),
            'slug': automation.slug,
            'workflow_version': workflow.version,
            'message': f"Workflow '{automation.name}' created successfully!"
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        responses=WorkflowDetailSerializer,
        description="Get workflow details including graph."
    )
    def retrieve(self, request, pk=None):
        """Get workflow details."""
        automation = self.get_object(pk)
        
        workflow = automation.workflows.filter(is_live=True).last()
        if not workflow:
            return Response({'error': 'No workflow found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'id': str(automation.id),
            'name': automation.name,
            'slug': automation.slug,
            'graph': workflow.graph.get('ui_graph', workflow.graph),
        })
    
    @extend_schema(
        request=WorkflowUpdateRequestSerializer,
        responses=WorkflowUpdateResponseSerializer,
        description="Update workflow by creating a new version."
    )
    def update(self, request, pk=None):
        """
        Update workflow.
        
        Creates a new workflow version (immutable history).
        """
        automation = self.get_object(pk)
        
        serializer = WorkflowUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        service.update_workflow(
            automation=automation,
            graph=serializer.validated_data['graph'],
            name=serializer.validated_data.get('name', automation.name),
            created_by=request.user.username
        )
        
        return Response({
            'id': str(automation.id),
            'message': 'Workflow updated successfully!'
        })

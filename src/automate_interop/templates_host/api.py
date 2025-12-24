from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

class TemplateHostViewSet(viewsets.ViewSet):
    """
    Implements n8n Custom Template Library API.
    """
    permission_classes = [permissions.AllowAny] # Secured by internal net or token if needed

    @action(detail=False, methods=["get"])
    def workflows(self, request):
        # Return list of template workflows
        # Schema must match n8n expectation
        return Response({
            "data": [],
            "nextCursor": None
        })

    @action(detail=False, methods=["get"], url_path="workflows/(?P<pk>[^/.]+)")
    def workflow_detail(self, request, pk=None):
        return Response({"id": pk, "name": "Stub Template", "nodes": [], "connections": {}})

    @action(detail=False, methods=["get"])
    def collections(self, request):
        return Response({"data": []})

    @action(detail=False, methods=["get"])
    def health(self, request):
        return Response({"status": "ok"})

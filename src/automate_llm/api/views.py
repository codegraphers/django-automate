from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .permissions import CanManagePrompts, CanRunRuns, CanViewRuns
from .serializers import LlmRunCreateSerializer


class PromptViewSet(viewsets.ViewSet):
    permission_classes = [CanManagePrompts]
    # TODO: list/create/get + create version + publish + compile-preview

class RunViewSet(viewsets.ViewSet):
    permission_classes = [CanViewRuns]

    def list(self, request):
        # TODO: read from ORM store (redacted)
        return Response({"items": [], "page": {"next_cursor": None, "limit": 50}})

    def retrieve(self, request, pk=None):
        # TODO
        return Response({"id": int(pk), "status": "queued"})

    def create(self, request):
        ser = LlmRunCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        # TODO: call RunService.create_run + optionally execute
        return Response({"status": "queued"}, status=201)

    @action(detail=True, methods=["post"], permission_classes=[CanRunRuns])
    def execute(self, request, pk=None):
        # TODO: enqueue outbox
        return Response({"id": int(pk), "status": "queued"})

    @action(detail=True, methods=["post"], permission_classes=[CanRunRuns])
    def cancel(self, request, pk=None):
        # TODO
        return Response({"id": int(pk), "status": "cancelled"})

    @action(detail=True, methods=["post"], permission_classes=[CanRunRuns])
    def replay(self, request, pk=None):
        # TODO: policy gated
        return Response({"status": "queued"}, status=201)

class EvalDatasetViewSet(viewsets.ViewSet):
    # TODO CRUD
    pass

class EvalRunViewSet(viewsets.ViewSet):
    # TODO create/get
    pass

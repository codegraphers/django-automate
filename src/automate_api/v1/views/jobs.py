import json
import time

from django.http import StreamingHttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import decorators, viewsets
from rest_framework.response import Response

from automate_core.jobs.models import Job, JobEvent, JobStatusChoices

from ..auth import BearerTokenAuthentication
from ..pagination import CursorPagination
from ..permissions import IsAuthenticatedAndTenantScoped
from ..serializers.jobs import CancelResponse, JobSerializer
from ..throttling import TenantRateThrottle, TokenRateThrottle


def sse_format(event: str, data: str, event_id: int | None = None) -> str:
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    for line in data.splitlines():
        lines.append(f"data: {line}")
    lines.append("")  # blank line ends the event
    return "\n".join(lines) + "\n"

class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Jobs resource with SSE streaming.
    """
    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticatedAndTenantScoped]
    pagination_class = CursorPagination
    throttle_classes = [TenantRateThrottle, TokenRateThrottle]

    def get_queryset(self):
        qs = super().get_queryset()
        principal = getattr(self.request, "principal", None)
        if principal:
            qs = qs.filter(tenant_id=principal.tenant_id)
        return qs

    @extend_schema(request=None, responses=CancelResponse)
    @decorators.action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        job = self.get_object()
        # Mark canceled in DB (simplification)
        job.status = JobStatusChoices.FAILED # Real cancel logic is complex
        job.save()
        return Response({"job_id": job.id, "canceled": True})

    @extend_schema(
        parameters=[
            OpenApiParameter(name="last_seq", required=False, type=int, description="Start streaming after this seq."),
        ],
        responses=None,
    )
    @decorators.action(detail=True, methods=["get"])
    def events(self, request, pk=None):
        """
        Stream job events via SSE.
        """
        job = self.get_object()
        last_seq = int(request.query_params.get("last_seq", "0"))

        def gen():
            seq = last_seq
            # 1. Replay history
            history = JobEvent.objects.filter(job=job, seq__gt=last_seq).order_by("seq")
            for evt in history:
                yield sse_format(f"job.{evt.type}", json.dumps(evt.data), event_id=evt.seq)
                seq = max(seq, evt.seq)

            # 2. Stream live (Simulated simply here by waiting/polling)
            # In production, use redis pubsub or listen_db_changes
            start = time.time()
            max_seconds = 1 # Short for test/demo (was 60)

            while True:
                now = time.time()
                if now - start > max_seconds:
                     yield sse_format("job.stream.close", '{"reason":"timeout"}')
                     break

                # Check for new events
                new_events = JobEvent.objects.filter(job=job, seq__gt=seq).order_by("seq")
                for evt in new_events:
                     yield sse_format(f"job.{evt.type}", json.dumps(evt.data), event_id=evt.seq)
                     seq = evt.seq

                time.sleep(1) # Poll interval

        resp = StreamingHttpResponse(gen(), content_type="text/event-stream")
        resp["Cache-Control"] = "no-cache"
        resp["X-Accel-Buffering"] = "no"
        return resp

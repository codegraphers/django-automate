import json
import time

from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import decorators, mixins, serializers, status, viewsets
from rest_framework.response import Response

from automate_core.jobs.models import Job, JobEvent, JobStatusChoices

from ..auth import BearerTokenAuthentication

# We might need an adapter factory or DI here later.
# For now, cancellation just updates DB, generic worker handles it.
from ..permissions import IsTenantMember


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id", "tenant_id", "kind", "topic", "status",
            "created_at", "updated_at", "result_summary", "error_redacted"
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class JobViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsTenantMember] # + HasScope via method decorators if needed

    def get_queryset(self):
        # Enforce tenant isolation if user has tenant_id
        # For now, MVP assumes superuser or open
        return super().get_queryset()

    @extend_schema(request=None, responses={200: JobSerializer})
    @decorators.action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        job = self.get_object()
        if job.status in [JobStatusChoices.SUCCEEDED, JobStatusChoices.FAILED, JobStatusChoices.CANCELED]:
            return Response({"status": "ignored", "message": "Job already terminal"}, status=status.HTTP_200_OK)

        job.status = JobStatusChoices.CANCELED
        job.save()
        # Optionally call queue.cancel() if backend_task_id exists

        return Response(self.get_serializer(job).data)

    @extend_schema(summary="Stream job events (SSE)")
    @decorators.action(detail=True, methods=["get"])
    def events(self, request, pk=None):
        """
        Server-Sent Events (SSE) stream for job progress.
        Client should reconnect with Last-Event-ID if stream breaks.
        """
        job = self.get_object()

        def event_stream():
            last_seq = int(request.headers.get("Last-Event-ID", 0))

            # Send initial state
            yield f"event: job.status\ndata: {json.dumps({'status': job.status})}\n\n"

            # Poll for new events (MVP polling, Prod use LISTEN/NOTIFY or Redis)
            # 60s max duration
            start_time = time.time()
            while time.time() - start_time < 60:
                events = JobEvent.objects.filter(job=job, seq__gt=last_seq).order_by("seq")
                for evt in events:
                    last_seq = evt.seq
                    payload = {
                        "seq": evt.seq,
                        "type": evt.type,
                        "data": evt.data,
                        "created_at": evt.created_at.isoformat()
                    }
                    yield f"id: {evt.seq}\nevent: job.{evt.type}\ndata: {json.dumps(payload)}\n\n"

                # Check if job done
                job.refresh_from_db()
                if job.status in [JobStatusChoices.SUCCEEDED, JobStatusChoices.FAILED, JobStatusChoices.CANCELED]:
                    # Send one last status update then close
                    yield f"event: job.status\ndata: {json.dumps({'status': job.status})}\n\n"
                    break

                time.sleep(1) # Polling interval
                # Keepalive
                yield ": heartbeat\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no" # Nginx
        return response

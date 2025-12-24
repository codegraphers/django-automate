import logging
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .serializers import ModalRunRequestSerializer, ModalResultSerializer, ModalJobSerializer
from automate_modal.engine import engine
from automate_modal.contracts import StreamEvent

logger = logging.getLogger(__name__)

# TODO: Add specific permissions (RBAC)

class EndpointRunView(APIView):
    """
    Synchronous execution of a modal capability.
    POST /api/modal/{slug}/run
    """
    # permission_classes = [IsAuthenticated] # Configurable

    def post(self, request, slug):
        serializer = ModalRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            # Execute via engine
            result = engine.execute(
                endpoint_slug=slug,
                task_type=data['task_type'],
                req=data['input'],
                actor_id=str(request.user.id) if request.user.is_authenticated else "anon"
            )
            
            # Serialize result
            resp_serializer = ModalResultSerializer(result)
            return Response(resp_serializer.data)
            
        except Exception as e:
            logger.exception(f"Run failed for {slug}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EndpointStreamView(APIView):
    """
    Streaming execution via Server-Sent Events (SSE).
    POST /api/modal/{slug}/stream
    """
    
    def post(self, request, slug):
        serializer = ModalRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        def event_stream():
            try:
                iterator = engine.stream(
                    endpoint_slug=slug,
                    task_type=data['task_type'],
                    req=data['input'],
                    actor_id=str(request.user.id) if request.user.is_authenticated else "anon"
                )
                
                for event in iterator:
                    # Format as SSE
                    import json
                    # We manually serialize the StreamEvent dataclass
                    payload = {
                        "type": event.type,
                        "data": event.data,
                        "ts": event.ts
                    }
                    yield f"event: modal\ndata: {json.dumps(payload)}\n\n"
                    
            except Exception as e:
                import json
                yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


class EndpointJobView(APIView):
    """
    Submit an asynchronous job.
    POST /api/modal/{slug}/jobs
    """
    
    def post(self, request, slug):
        serializer = ModalRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            job_id = engine.submit_job(
                endpoint_slug=slug,
                task_type=data['task_type'],
                req=data['input'],
                actor_id=str(request.user.id) if request.user.is_authenticated else "anon"
            )
            
            return Response({"job_id": job_id, "status": "queued"}, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Job submission failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobStatusView(APIView):
    """
    Get job status.
    GET /api/modal/jobs/{job_id}
    """
    def get(self, request, job_id):
        # In a real app, query by job_id (and check perm)
        # For prototype, we'll assume job_id is unique enough or check tenant
        from automate_modal.models import ModalJob
        
        try:
            job = ModalJob.objects.get(job_id=job_id)
            serializer = ModalJobSerializer(job)
            return Response(serializer.data)
        except ModalJob.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class JobEventsView(APIView):
    """
    Stream job events via SSE.
    GET /api/modal/jobs/{job_id}/events
    """
    def get(self, request, job_id):
        # Mock implementation for now as we don't have event persistence yet
        # Real impl would poll DB or Redis
        
        def event_stream():
            # Initial status
            import json
            yield f"event: connect\ndata: {json.dumps({'job_id': job_id})}\n\n"
            
            # TODO: Poll logic
        
        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


class ArtifactDownloadView(APIView):
    """
    Download artifact.
    GET /api/modal/artifacts/{artifact_id}/download
    """
    def get(self, request, artifact_id):
        from automate_modal.models import ModalArtifact
        from automate_modal.engine import engine
        
        try:
            artifact = ModalArtifact.objects.get(id=artifact_id)
            # Check perm (omitted for speed)
            
            # Generate pre-signed URL (if S3) or redirect/stream if local
            # For now, let's assume we redirect to the BlobStore URL
            url = engine.blob.generate_presigned_url(artifact.uri)
            
            return Response({"url": url}) # Check redirection logic
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

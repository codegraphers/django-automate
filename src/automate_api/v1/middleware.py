import uuid

from django.utils.deprecation import MiddlewareMixin

CORRELATION_HEADER = "HTTP_X_CORRELATION_ID"
RESPONSE_HEADER = "X-Correlation-ID"

class CorrelationIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        cid = request.META.get(CORRELATION_HEADER) or str(uuid.uuid4())
        request.correlation_id = cid

    def process_response(self, request, response):
        cid = getattr(request, "correlation_id", None)
        if cid:
            response[RESPONSE_HEADER] = cid
        return response

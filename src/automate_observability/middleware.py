import uuid

from .context import set_trace_id


class TraceIdMiddleware:
    """
    Ensures every request has a trace_id.
    Reads X-Trace-ID header if present (for propagation), or generates new UUID.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        set_trace_id(trace_id)

        # Attach to request for view usage
        request.trace_id = trace_id

        response = self.get_response(request)

        # Echo back in response header
        response["X-Trace-ID"] = trace_id
        return response

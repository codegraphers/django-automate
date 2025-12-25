import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

def api_exception_handler(exc, context):
    request = context.get("request")
    cid = getattr(request, "correlation_id", None) if request else None
    resp = exception_handler(exc, context)

    if resp is None:
        # Unhandled exception (500)
        logger.exception(f"Unhandled API exception: {exc}")
        return Response(
            {"error": {"code": "internal", "message": "Internal error", "correlation_id": cid}},
            status=500
        )

    # Wrap DRF’s default error into your canonical envelope
    message = "Request failed"
    code = "request_failed"

    if isinstance(resp.data, dict):
        detail = resp.data.get("detail")
        message = str(detail) if detail else str(resp.data)
        if hasattr(detail, "code"):
            code = detail.code
    elif isinstance(resp.data, list):
         message = str(resp.data)
         code = "validation_error"

    return Response(
        {"error": {"code": code, "message": message, "correlation_id": cid}},
        status=resp.status_code,
        headers=resp.headers,
    )

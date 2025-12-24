import logging
import uuid

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

def standard_exception_handler(exc, context):
    """
    Custom exception handler that standardizes all error responses
    to the format:
    {
        "error": {
            "code": "error_code",
            "message": "Human readable message",
            "correlation_id": "..."
        }
    }
    """
    # Call REST framework's default exception handler first to get the standard Response
    response = exception_handler(exc, context)

    # If we got a response, wrap it locally
    correlation_id = _get_correlation_id(context['request'])

    if response is not None:
        data = response.data

        # Handle DRF's standard validation error dict
        if isinstance(data, dict):
            # If it's a detail message, use it
            message = data.get("detail", str(data))
            code = data.get("code", "error")
        elif isinstance(data, list):
            message = str(data)
            code = "validation_error"
        else:
            message = str(data)
            code = "error"

        response.data = {
            "error": {
                "code": code,
                "message": message,
                "correlation_id": correlation_id,
            }
        }
        return response

    # If response is None, it's an unhandled exception (500)
    logger.exception(f"Unhandled API exception: {exc}")

    return Response(
        {
            "error": {
                "code": "internal_error",
                "message": "An internal error occurred.",
                "correlation_id": correlation_id
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

def _get_correlation_id(request):
    """Safe extraction of correlation ID."""
    return getattr(request, "correlation_id", str(uuid.uuid4()))

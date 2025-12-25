from typing import Any


class AutomateError(Exception):
    """Canonical base exception for all automation errors."""
    def __init__(
        self,
        code: str,
        message: str,
        is_transient: bool = False,
        retry_after_s: int | None = None,
        provider: str | None = None,
        http_status: int | None = None,
        details_redacted: dict[str, Any] | None = None,
        original_exception: Exception | None = None
    ):
        self.code = code
        self.message = message
        self.is_transient = is_transient
        self.retry_after_s = retry_after_s
        self.provider = provider
        self.http_status = http_status
        self.details_redacted = details_redacted or {}
        self.original_exception = original_exception
        super().__init__(message)

class ErrorCodes:
    UNAUTHORIZED = "unauthorized"           # Bad/missing API key
    FORBIDDEN = "forbidden"                 # Permission denied / policy blocked
    NOT_FOUND = "not_found"                 # Model/Resource missing
    INVALID_REQUEST = "invalid_request"     # Schema violation, bad args
    RATE_LIMITED = "rate_limited"           # 429
    QUOTA_EXCEEDED = "quota_exceeded"       # Billing limits
    TIMEOUT = "timeout"                     # Network/Processing timeout
    PROVIDER_UNAVAILABLE = "provider_unavailable" # 5xx or connection error
    CONTENT_BLOCKED = "content_blocked"     # Safety filters
    CONFLICT = "conflict"                   # Idempotency / state conflict
    INTERNAL = "internal"                   # Unexpected implementation bug
    DEPENDENCY = "dependency"               # Downstream system failure

def requests_exception_to_automate_error(exc: Any, provider: str) -> AutomateError:
    """Helper to Map requests/httpx exceptions to AutomateError."""
    # This is a generic helper.
    # Real implementations might inspect response.status_code if available.
    msg = str(exc)

    # Check for basic request types strictly if library is available,
    # but often we just rely on the object attrs.
    if hasattr(exc, 'response') and exc.response is not None:
        status = exc.response.status_code
        if status == 401:
            return AutomateError(ErrorCodes.UNAUTHORIZED, "Unauthorized", False, provider=provider, http_status=401, original_exception=exc)
        if status == 403:
            return AutomateError(ErrorCodes.FORBIDDEN, "Forbidden", False, provider=provider, http_status=403, original_exception=exc)
        if status == 404:
            return AutomateError(ErrorCodes.NOT_FOUND, "Not Found", False, provider=provider, http_status=404, original_exception=exc)
        if status == 429:
            # Try to parse Retry-After
            retry = None
            if hasattr(exc.response, 'headers'):
                 ra = exc.response.headers.get('Retry-After')
                 if ra and ra.isdigit(): retry = int(ra)
            return AutomateError(ErrorCodes.RATE_LIMITED, "Rate Limited", True, retry_after_s=retry, provider=provider, http_status=429, original_exception=exc)
        if status >= 500:
             return AutomateError(ErrorCodes.PROVIDER_UNAVAILABLE, f"Provider Error {status}", True, provider=provider, http_status=status, original_exception=exc)

    # Connection errors
    # For now catch-all transient
    return AutomateError(ErrorCodes.PROVIDER_UNAVAILABLE, f"Connection Failed: {msg}", True, provider=provider, original_exception=exc)

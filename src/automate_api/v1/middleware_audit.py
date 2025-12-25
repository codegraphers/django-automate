import json
import logging

from django.utils.deprecation import MiddlewareMixin

from automate_core.security.redaction import redact
from automate_governance.models import AuditLog

logger = logging.getLogger(__name__)

class AuditMiddleware(MiddlewareMixin):
    """
    Auto-audit modifying API requests.
    Redacts logging payload securely.
    """
    def process_request(self, request):
        # Eagerly read body for modifying requests to cache it for audit
        # This allows accessing it in process_response even if DRF consumed stream
        if request.method in ("POST", "PUT", "PATCH") and request.content_type == "application/json":
            try:
                # Accessing .body forces Django to read and cache it
                _ = request.body
            except Exception:
                pass

    def process_response(self, request, response):
        # 1. Filter: Valid for API only?
        if not request.path.startswith("/api/"):
            return response

        # 2. Filter: Safe methods? (Optional: audit GETs if needed for read-access logs)
        # For V1, we log modifying actions + Auth failures
        is_modifying = request.method in ("POST", "PUT", "PATCH", "DELETE")
        is_error = response.status_code >= 400

        should_audit = is_modifying or is_error

        if not should_audit:
            return response

        try:
            principal = getattr(request, "principal", None)

            # Actor Resolution
            actor = {
                "type": "anonymous",
                "id": "unknown",
                "name": "unknown"
            }
            if principal:
                actor = {
                    "type": "token", # Assume token for now
                    "id": principal.user_id,
                    "name": principal.user_id, # Or token name
                    "tenant_id": principal.tenant_id
                }

            tenant_id = getattr(principal, "tenant_id", "public")

            # Payload Capture & Redaction
            payload_redacted = {}
            if request.content_type == "application/json":
                try:
                    # After process_request force-read, .body should be available
                    if request.body:
                        raw_data = json.loads(request.body)
                        payload_redacted = redact(raw_data)
                except Exception:
                     payload_redacted = {"_error": "Invalid or unavailable JSON body"}

            # Action Name
            # Heuristic: method + path-template
            # Ideal: viewset should annotate the request with action name
            # For now: RAW path
            action_name = f"{request.method} {request.path}"

            AuditLog.objects.create(
                tenant_id=tenant_id,
                actor=actor,
                action=action_name,
                resource={"path": request.path},
                result="success" if response.status_code < 400 else "failure",
                correlation_id=getattr(request, "correlation_id", None),
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                payload_redacted=payload_redacted
            )
        except Exception as e:
            # Audit logging failing should NOT break the API response
            # But we must log critical failure
            logger.error(f"Failed to write audit log: {e}", exc_info=True)

        return response

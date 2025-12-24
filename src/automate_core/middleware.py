import logging
import uuid
from django.utils.deprecation import MiddlewareMixin
from .context import set_current_tenant, set_current_actor, set_current_correlation_id

logger = logging.getLogger(__name__)

class AutomateContextMiddleware(MiddlewareMixin):
    """
    Extracts multi-tenancy and tracing context from headers or session.
    Sets global ContextVars for use in signals, logs, and deep logic.
    """

    def process_request(self, request):
        # 1. Tenant Extraction
        # Priority: Header > User Attribute > Default
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id and request.user.is_authenticated:
            # TODO: Add tenant_id to user model or profile
            # tenant_id = getattr(request.user, "tenant_id", "default")
            tenant_id = "default" 
            
        if not tenant_id:
            tenant_id = "default" # Fallback for dev/simple setups
            
        set_current_tenant(tenant_id)
        
        # 2. Actor Extraction
        if request.user.is_authenticated:
            set_current_actor(str(request.user.id))
        else:
            set_current_actor("anonymous")

        # 3. Correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_current_correlation_id(correlation_id)
        
        # Attach to request for view convenience
        request.tenant_id = tenant_id
        request.correlation_id = correlation_id

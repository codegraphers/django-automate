from rest_framework.throttling import SimpleRateThrottle


class TenantRateThrottle(SimpleRateThrottle):
    scope = "tenant"
    def get_cache_key(self, request, view):
        p = getattr(request, "principal", None)
        if not p:
            return None
        return f"tenant:{p.tenant_id}"

class TokenRateThrottle(SimpleRateThrottle):
    scope = "token"
    def get_cache_key(self, request, view):
        p = getattr(request, "principal", None)
        if not p:
            return None
        return f"token:{p.token_id}"

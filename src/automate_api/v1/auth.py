from dataclasses import dataclass

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


@dataclass
class Principal:
    user_id: str
    tenant_id: str
    scopes: set[str]
    token_id: str

def _parse_bearer(auth_header: str) -> str:
    if not auth_header:
        raise AuthenticationFailed("Missing Authorization header")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationFailed("Invalid Authorization header")
    return parts[1]

class BearerTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization")
        if not auth:
            return None # Allow other auth classes or unauthenticated if permitted

        token = _parse_bearer(auth)

        # TODO: lookup token in DB; verify hash; check expiry; load tenant/scopes
        # For now, we mock a principal for specific test tokens to unblock development
        if token == "test":
            principal = Principal(
                user_id="u_test",
                tenant_id="t1",
                scopes={"*"},
                token_id="tok_test"
            )
        else:
            # raise AuthenticationFailed("Token validation not implemented")
            # For strictness we fail here if header is present but invalid/unknown
            raise AuthenticationFailed("Invalid token")

        request.principal = principal
        # Propagate to underlying Django request for middleware
        if hasattr(request, "_request"):
            request._request.principal = principal

        return (principal, token)

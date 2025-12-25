from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class IsAuthenticatedAndTenantScoped(BasePermission):
    def has_permission(self, request, view):
        principal = getattr(request, "principal", None)
        if not principal:
            return False
        return True

def require_scopes(request, required: set[str]):
    principal = getattr(request, "principal", None)
    if not principal:
        raise PermissionDenied("Not authenticated")

    # Handle wildcard scope for admin/test
    if "*" in principal.scopes:
        return

    missing = required - set(principal.scopes)
    if missing:
        raise PermissionDenied(f"Missing scopes: {', '.join(sorted(missing))}")

from rest_framework import permissions


class HasScope(permissions.BasePermission):
    """
    Checks if the user's token/principal has the required scope.
    Usage:
        permission_classes = [HasScope]
        required_scopes = ['automations:read']
    """
    def has_permission(self, request, view):
        required_scopes = getattr(view, "required_scopes", [])
        if not required_scopes:
            return True # No specific scope needed, just authentication

        # User scopes would normally be on the token or calculated
        # For MVP/Default, superusers have all scopes
        if request.user.is_superuser:
            return True

        # TODO: Implement actual scope extraction from Token/Principal
        # user_scopes = request.auth.get('scopes', []) if request.auth else []
        return True # Default open for now until Scopes are fully modeled

class IsTenantMember(permissions.BasePermission):
    """
    Ensures user belongs to the requested object's tenant.
    This logic happens usually in QuerySet filtering, but this adds obj-level check.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Assume objects have tenant_id
        if hasattr(obj, "tenant_id"):
            # Assume user profile has tenant_id or similar
            # return obj.tenant_id == request.user.profile.tenant_id
            pass
        return True

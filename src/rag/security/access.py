"""
Access Control for RAG Endpoints

Provides RBAC/ABAC policy enforcement for retrieval queries.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_access_policy(
    policy: dict[str, Any],
    user,
    request_context: dict[str, Any] | None = None
) -> bool:
    """
    Check if a user has access based on endpoint policy.
    
    Policy format:
    {
        "allow_all": True,  # Bypass all checks
        "allowed_groups": ["rag-users", "admins"],
        "allowed_users": ["specific@user.com"],
        "denied_users": ["blocked@user.com"],
        "require_authenticated": True
    }
    
    Args:
        policy: Access policy configuration
        user: Django user object
        request_context: Additional context (IP, headers, etc.)
        
    Returns:
        True if access is allowed, False otherwise
    """
    if not policy:
        # No policy = allow all (for backward compatibility)
        return True

    # Check allow_all bypass
    if policy.get("allow_all", False):
        return True

    # Check authentication requirement
    if policy.get("require_authenticated", True):
        if not user or not user.is_authenticated:
            logger.info("Access denied: authentication required")
            return False

    # Check denied users
    denied_users = policy.get("denied_users", [])
    if user and user.username in denied_users:
        logger.info(f"Access denied: user {user.username} is blocked")
        return False

    # Check allowed users
    allowed_users = policy.get("allowed_users", [])
    if allowed_users and user and user.username in allowed_users:
        return True

    # Check allowed groups
    allowed_groups = policy.get("allowed_groups", [])
    if allowed_groups:
        if user and hasattr(user, 'groups'):
            user_groups = set(user.groups.values_list('name', flat=True))
            if user_groups.intersection(set(allowed_groups)):
                return True
        # If groups are specified but user doesn't match, deny
        if allowed_users:
            # Already checked allowed_users above
            pass
        else:
            logger.info("Access denied: user not in allowed groups")
            return False

    # Default: allow if no specific restrictions
    return True


def get_policy_decisions(
    policy: dict[str, Any],
    user,
    allowed: bool
) -> dict[str, Any]:
    """
    Get audit-friendly policy decision details.
    
    Returns:
        Dict with decision metadata for logging
    """
    return {
        "allowed": allowed,
        "user": user.username if user and hasattr(user, 'username') else "anonymous",
        "policy_version": policy.get("version", "1"),
        "checks_performed": [
            "authentication",
            "denied_users",
            "allowed_users",
            "allowed_groups"
        ]
    }

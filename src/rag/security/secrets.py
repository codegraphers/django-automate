"""
SecretRef Resolver

Resolves secret references in various formats:
- env://VAR_NAME - Environment variable
- db://secret_name - Database-stored secret (via SecretStore model if exists)
- vault://path/to/secret - HashiCorp Vault (future)
- raw://value - Raw value (NOT recommended, for testing only)

All credentials in RAG should use SecretRef, never raw secrets.
"""
import logging
import os

logger = logging.getLogger(__name__)


class SecretRefError(Exception):
    """Raised when secret resolution fails."""
    pass


def resolve_secret_ref(ref: str) -> str | None:
    """
    Resolve a secret reference to its actual value.
    
    Supported formats:
    - env://VAR_NAME - Read from environment variable
    - db://name - Read from SecretStore model (if available)
    - raw://value - Use raw value (testing only!)
    
    Args:
        ref: SecretRef URI string
        
    Returns:
        Resolved secret value, or None if not found
        
    Raises:
        SecretRefError: If format is invalid or resolution fails
    """
    if not ref:
        return None

    if not isinstance(ref, str):
        raise SecretRefError(f"SecretRef must be a string, got {type(ref)}")

    # Parse the URI scheme
    if "://" not in ref:
        raise SecretRefError(f"Invalid SecretRef format: {ref}. Expected scheme://value")

    scheme, value = ref.split("://", 1)
    scheme = scheme.lower()

    if scheme == "env":
        return _resolve_env(value)
    elif scheme == "db":
        return _resolve_db(value)
    elif scheme == "raw":
        logger.warning("Using raw:// secret - NOT recommended for production")
        return value
    elif scheme == "vault":
        return _resolve_vault(value)
    else:
        raise SecretRefError(f"Unknown SecretRef scheme: {scheme}")


def _resolve_env(var_name: str) -> str | None:
    """Resolve from environment variable."""
    value = os.environ.get(var_name)
    if value is None:
        logger.warning(f"Environment variable not found: {var_name}")
    return value


def _resolve_db(name: str) -> str | None:
    """Resolve from database SecretStore."""
    try:
        # Try to use automate's SecretStore if available
        from automate.models import SecretStore
        secret = SecretStore.objects.filter(name=name).first()
        if secret:
            return secret.get_value()
        logger.warning(f"Secret not found in database: {name}")
        return None
    except ImportError:
        logger.warning("SecretStore model not available, falling back to None")
        return None
    except Exception as e:
        logger.error(f"Failed to resolve db secret: {e}")
        return None


def _resolve_vault(path: str) -> str | None:
    """Resolve from HashiCorp Vault (future implementation)."""
    # TODO: Implement Vault integration
    logger.warning(f"Vault integration not yet implemented: {path}")
    raise SecretRefError("Vault integration not yet implemented")


def redact_secret(value: str, show_chars: int = 4) -> str:
    """
    Redact a secret value for safe logging.
    
    Args:
        value: Secret value to redact
        show_chars: Number of characters to show at the end
        
    Returns:
        Redacted string like "****abcd"
    """
    if not value:
        return "[empty]"

    if len(value) <= show_chars:
        return "*" * len(value)

    return "*" * (len(value) - show_chars) + value[-show_chars:]

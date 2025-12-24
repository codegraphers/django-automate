from contextvars import ContextVar

# Global context for the current request/execution lifecycle
_current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)
_current_actor_id: ContextVar[str | None] = ContextVar("current_actor_id", default=None)
_current_correlation_id: ContextVar[str | None] = ContextVar("current_correlation_id", default=None)


def set_current_tenant(tenant_id: str):
    return _current_tenant_id.set(tenant_id)


def get_current_tenant() -> str | None:
    return _current_tenant_id.get()


def set_current_actor(actor_id: str):
    return _current_actor_id.set(actor_id)


def get_current_actor() -> str | None:
    return _current_actor_id.get()


def set_current_correlation_id(correlation_id: str):
    return _current_correlation_id.set(correlation_id)


def get_current_correlation_id() -> str | None:
    return _current_correlation_id.get()


class TenantContext:
    """
    Context manager for temporarily switching tenant.
    Usage:
        with TenantContext("tenant_123"):
            # do work
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.token = None

    def __enter__(self):
        self.token = set_current_tenant(self.tenant_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            _current_tenant_id.reset(self.token)

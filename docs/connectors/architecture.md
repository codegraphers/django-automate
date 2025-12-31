# Connector Architecture

Django Automate provides two connector patterns for different use cases.

## Pattern 1: BaseProvider (Recommended for Most Cases)

The unified provider pattern, used by LLM, RAG, Modal, and Connectors.

```python
from automate_connectors.providers.base import BaseProvider, ProviderContext

class MyServiceProvider(BaseProvider):
    name = "my_service"
    
    def execute(self, action: str, params: dict, context: ProviderContext) -> dict:
        # Implementation
        return {"result": "ok"}
```

**Use when:**
- Building LLM/RAG/Modal integrations
- Need unified secret resolution via `SecretRef`
- Want consistent observability/audit
- Building reusable, enterprise-grade connectors

**Features:**
- `ProviderContext` with tenant, correlation_id, secrets
- Automatic RBAC integration
- Structured `ActionSpec` definitions

---

## Pattern 2: ConnectorAdapter (Simple Integrations)

Lightweight adapter for simple webhook/API integrations.

```python
from automate_connectors.adapters.base import ConnectorAdapter

class MyWebhookAdapter(ConnectorAdapter):
    def send(self, payload: dict) -> dict:
        # Simple HTTP call
        return {"status": "sent"}
```

**Use when:**
- Simple webhook/notification integrations
- One-off, project-specific connectors
- Minimal ceremony needed

---

## Decision Guide

| Requirement | BaseProvider | ConnectorAdapter |
|-------------|--------------|------------------|
| Multi-tenant | ✅ | ❌ |
| Secret management | ✅ SecretRef | Manual |
| Audit/observability | ✅ Built-in | Manual |
| Complexity | Higher | Lower |
| Reusability | High | Project-specific |

## Registration

Both patterns support entrypoint-based discovery:

```toml
# pyproject.toml
[project.entry-points."automate.connectors"]
my_service = "my_package.connectors:MyServiceProvider"
```

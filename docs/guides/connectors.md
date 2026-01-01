# Building Connectors

This guide shows how to build connectors for Django Automate.

---

## Quick Start

Connectors extend the `ConnectorAdapter` base class:

```python
from automate_connectors.adapters.base import ConnectorAdapter

class MyServiceAdapter(ConnectorAdapter):
    """Adapter for MyService integration."""
    
    name = "my_service"
    version = "1.0.0"
    
    def connect(self) -> bool:
        """Test connectivity to the service."""
        # Return True if service is reachable
        return True
    
    def execute(self, action: str, payload: dict) -> dict:
        """Execute an action on the service."""
        if action == "send_message":
            return self._send_message(payload)
        raise ValueError(f"Unknown action: {action}")
    
    def _send_message(self, payload: dict) -> dict:
        # Implementation here
        return {"status": "sent"}
```

---

## Registration

Register your adapter in the connector registry:

```python
from automate_connectors.registry import connector_registry

connector_registry.register("my_service", MyServiceAdapter)
```

Or use entry points in `pyproject.toml`:

```toml
[project.entry-points."automate.connectors"]
my_service = "my_package.adapters:MyServiceAdapter"
```

---

## Testing

Use the official test harness:

```python
from automate_connectors.testing import ConnectorTestCase

class TestMyServiceAdapter(ConnectorTestCase):
    adapter_class = MyServiceAdapter
    
    def test_connect(self):
        adapter = self.get_adapter()
        assert adapter.connect() is True
    
    def test_send_message(self):
        adapter = self.get_adapter()
        result = adapter.execute("send_message", {"text": "Hello"})
        assert result["status"] == "sent"
```

---

## Built-in Adapters

Django Automate includes these adapters:

| Adapter | Module | Description |
|---------|--------|-------------|
| Slack | `automate_connectors.adapters.slack` | Slack messaging |
| Logging | `automate_connectors.adapters.logging` | Debug logging |

---

## Adapter Lifecycle

```mermaid
flowchart LR
    A[Register] --> B[Instantiate]
    B --> C[connect()]
    C --> D{Connected?}
    D -->|Yes| E[execute()]
    D -->|No| F[Retry/Error]
    E --> G[Return Result]
```

---

## Best Practices

1. **Single Responsibility**: One adapter per external service
2. **Idempotent Actions**: `execute()` should be safe to retry
3. **Structured Errors**: Raise `ConnectorError` subclasses
4. **Health Checks**: Implement `connect()` for monitoring
5. **Secrets**: Use `ConnectionProfile` for credentials

# Connector Architecture

Django Automate uses a single, canonical connector pattern.

---

## Canonical Pattern: ConnectorAdapter

All connectors inherit from `ConnectorAdapter`:

```python
from automate_connectors.adapters.base import ConnectorAdapter

class MyAdapter(ConnectorAdapter):
    name = "my_adapter"
    
    def connect(self) -> bool:
        return True
    
    def execute(self, action: str, payload: dict) -> dict:
        return {"result": "ok"}
```

---

## Key Components

| Component | Purpose |
|-----------|---------|
| `adapters.base.ConnectorAdapter` | Base class for all connectors |
| `registry.connector_registry` | Connector registration |
| `testing.ConnectorTestCase` | Official test harness |

---

## Documentation

See the full guide: [Building Connectors](../guides/connectors.md)

---

## Legacy Providers

> ⚠️ The `BaseProvider` pattern from the old `providers/` directory is deprecated.

Legacy examples are in `examples/legacy_connectors/` for reference only.

# Legacy Connector Providers

> ⚠️ **Note**: These files use the legacy provider pattern. For new connectors, use the canonical `ConnectorAdapter` approach.

See [Connector Guide](../../docs/guides/connectors.md) for the recommended approach.

## Files

- `slack.py` - Legacy Slack provider implementation
- `webhook.py` - Legacy webhook provider implementation

## Migration

To migrate a legacy provider to the canonical adapter pattern:

```python
# Legacy (don't use)
from automate_connectors.providers.base import BaseProvider

class MyProvider(BaseProvider):
    def execute(self, action, params, context):
        ...

# Canonical (use this)
from automate_connectors.adapters.base import ConnectorAdapter

class MyAdapter(ConnectorAdapter):
    name = "my_adapter"
    
    def connect(self) -> bool:
        return True
    
    def execute(self, action: str, payload: dict) -> dict:
        ...
```

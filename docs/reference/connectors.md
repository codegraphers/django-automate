# Connectors Reference

All connectors extend `ConnectorAdapter` from `automate_connectors.adapters.base`.

---

## ConnectorAdapter Base Class

```python
from automate_connectors.adapters.base import ConnectorAdapter

class MyAdapter(ConnectorAdapter):
    code = "my_adapter"
    name = "My Adapter"
    
    def validate_config(self, config: dict) -> ValidationResult:
        """Validate adapter configuration."""
        return ValidationResult(ok=True, errors=[])
    
    def execute(self, action: str, input_args: dict, ctx: dict) -> ConnectorResult:
        """Execute an action."""
        ...
```

### Key Methods

| Method | Description |
|--------|-------------|
| `validate_config()` | Validate configuration before use |
| `execute()` | Execute an action with input arguments |
| `normalize_error()` | Convert exceptions to ConnectorError |

---

## SlackAdapter

Send messages to Slack channels.

```python
from automate_connectors.adapters.slack import SlackAdapter

adapter = SlackAdapter()
result = adapter.execute(
    "send_message",
    {"channel": "#general", "message": "Hello!"},
    {"profile": {"encrypted_secrets": {"token": "xoxb-..."}}}
)
```

### Actions

| Action | Input | Description |
|--------|-------|-------------|
| `send_message` | `channel`, `message`, `blocks` | Post message to channel |

---

## LoggingAdapter

Debug adapter that logs all actions.

```python
from automate_connectors.adapters.logging import LoggingAdapter

adapter = LoggingAdapter()
result = adapter.execute("debug", {"data": "test"}, {})
```

---

## Building Custom Adapters

See [Building Connectors](../guides/connectors.md) for the full guide.

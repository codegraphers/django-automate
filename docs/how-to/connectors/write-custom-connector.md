# Writing a Custom Connector

To integrate with a proprietary internal system, you can write a custom Connector Adapter.

## 1. The Adapter Definition
Create a class inheriting from `ConnectorAdapter`.

```python
# my_app/adapters.py
from automate_connectors.adapters.base import ConnectorAdapter, ActionSpec
from automate_connectors.models import ConnectorError

class LegacyERPAdapter(ConnectorAdapter):
    code = "legacy_erp"
    name = "Legacy ERP System"
    description = "Integration with the on-prem SOAP ERP."

    # Define the inputs/outputs for the UI
    actions = {
        "create_order": ActionSpec(
            inputs={
                "customer_id": {"type": "string", "required": True},
                "items": {"type": "array", "required": True}
            },
            outputs={
                "order_id": {"type": "string"}
            }
        )
    }

    def execute(self, action: str, params: dict, context: dict):
        if action == "create_order":
            try:
                # context['secrets'] is automatically populated
                api_key = context['secrets'].get('API_KEY')
                
                result = self._soap_client.create_order(key=api_key, **params)
                return {"order_id": result.id}
            except Exception as e:
                # Wrap unknowns in NormalizedError
                raise ConnectorError(f"ERP Failed: {str(e)}", retryable=True)
                
        raise NotImplementedError(f"Action {action} unknown")
```

## 2. Registration
Register specific adapters in your `AppConfig` or via `entry_points`.

```python
from automate_connectors.registry import register_connector

@register_connector
class LegacyERPAdapter...
```

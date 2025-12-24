# How-To Guides

Task-oriented guides for common operations.

## Authoring Workflows

### Using the Visual Studio
1.  Navigate to `/studio/wizard/`.
2.  **Drafting**: Use the AI Copilot ("When a high value order comes in...") to generate a skeleton.
3.  **Refining**: Drag nodes to rearrange. Click a node to edit its JSON config properties.
4.  **Testing**: Use the **Rule Tester** tab to verify your logic conditions against sample JSON payloads.
5.  **Publishing**: Click "Publish". This creates a new active version of the workflow.

### Using JSON (Code-First)
Recommended for version-controlled workflows. Define your workflow in a JSON file and load it via management command:
```bash
python manage.py automate_import --file workflows/order_flow.json
```

## Secrets Management

### Rotating Secrets
1.  **Env Backend**: Update your environment variable (e.g., `AUTOMATE_STRIPE_KEY_V2`) and update the `SecretRef` in your workflow to point to the new key.
2.  **DB Backend**: Go to Admin > Governance > Stored Secrets. Use the "Rotate Secret" action to securely update the value without changing the reference key used in workflows.

### Masking in Admin
The Studio automatically masks secret values in the UI (showing `********`). Never hardcode secrets in the "Config" JSON fields. Always use `{"$secret": "KEY_NAME"}`.

## Building Custom Connectors

To add a proprietary internal system (e.g., "Legacy ERP"):

### 1. The Adapter Definition
Create a class inheriting from `ConnectorAdapter`.

```python
# my_app/adapters.py
from automate_connectors.adapters.base import ConnectorAdapter
from automate_connectors.models import ActionSpec, ConnectorError

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
                # context['secrets'] is automatically populated based on SecretRefs
                api_key = context['secrets'].get('API_KEY')
                
                result = self._soap_client.create_order(
                    key=api_key, 
                    **params
                )
                return {"order_id": result.id}
            except Exception as e:
                # Wrap unknowns in NormalizedError
                raise ConnectorError(f"ERP Failed: {str(e)}", retryable=True)
                
        raise NotImplementedError(f"Action {action} unknown")
```

### 2. Registration
Register specific adapters in your `AppConfig` or via `entry_points`.

**Method A: AppConfig**
```python
from django.apps import AppConfig
from automate_connectors.registry import register

class MyAppConfig(AppConfig):
    def ready(self):
        from .adapters import LegacyERPAdapter
        register(LegacyERPAdapter)
```

**Method B: Decorator**
```python
from automate_connectors.registry import register_connector

@register_connector
class LegacyERPAdapter...
```

## Operations

### Tuning Throughput
If your worker is lagging:
1.  **Increase Concurrency**: Run more worker processes.
2.  **Batch Size**: Increase `EXECUTION_BATCH_SIZE` in settings (Default: 10).
3.  **DB Optimization**: Ensure you are using Postgres and `SKIP LOCKED` is enabled (Automatic on supported DBs).

### Debugging Failures
1.  Go to **Execution Explorer**.
2.  Find the Failed run (Red status).
3.  Click the failed Step.
4.  View the **Output/Error** payload. It will contain the stack trace or error message provided by the connector.
5.  Check the **Audit Log** link for the exact timestamp and context of the failure.

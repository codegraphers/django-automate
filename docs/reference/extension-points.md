# Extension Points

This framework is designed to be extended. Below are all stable interfaces for plugins and customization.

## Table of Contents

1. [Provider Registry](#provider-registry)
2. [Secrets Backend](#secrets-backend)
3. [Connectors](#connectors)
4. [Admin Base Classes](#admin-base-classes)
5. [API Base Classes](#api-base-classes)
6. [Outbox Pattern](#outbox-pattern)
7. [Signal Handlers](#signal-handlers)
8. [Template System](#template-system)

---

## Provider Registry

- **Name**: `ProviderRegistry`
- **Stability**: **Stable**
- **Purpose**: Discovers and loads external capabilities (LLMs, Tools).
- **Interface**: `automate_core.providers.base.BaseProvider`

### How to Register

**Method 1: Settings**
```python
# settings.py
AUTOMATE_PROVIDERS = [
    'myapp.providers.MyCustomProvider',
]
```

**Method 2: Entry Points**
```toml
# pyproject.toml
[project.entry-points."django_automate.providers"]
my_provider = "myapp.providers:MyCustomProvider"
```

### Provider Interface

```python
from automate_core.providers.base import BaseProvider

class MyProvider(BaseProvider):
    key = "my_provider"
    display_name = "My Custom Provider"
    
    def __init__(self, config: dict, *, ctx: ProviderContext):
        self.config = config
        self.ctx = ctx
    
    @classmethod
    def config_schema(cls) -> type[BaseModel]:
        return MyProviderConfig
    
    def normalize_error(self, exc: Exception) -> Exception:
        return AutomateError(ErrorCodes.INTERNAL, str(exc))
```

---

## Secrets Backend

- **Name**: `SecretsBackend`
- **Stability**: **Stable**
- **Purpose**: Resolves sensitive credentials at runtime.
- **Interface**: `automate.secrets_backend.SecretsBackend`

### Implementation

```python
from automate_governance.secrets.interfaces import SecretsBackend

class VaultBackend(SecretsBackend):
    """HashiCorp Vault integration."""
    
    def get_secret(self, key: str) -> str:
        """Return the raw secret value."""
        # Connect to Vault
        response = self.vault_client.read(f"secret/data/{key}")
        if not response:
            raise SecretNotFoundError(key)
        return response['data']['value']
```

### Registration

```toml
# pyproject.toml
[project.entry-points."django_automate.secrets.backends"]
vault = "myapp.secrets:VaultBackend"
```

---

## Connectors

- **Name**: `Connector`
- **Stability**: **Beta**
- **Purpose**: Defines Actions and Triggers for external services.
- **Interface**: `automate_connectors.base.Connector`

### Connector Interface

```python
from automate_connectors.base import Connector, ActionSpec, TriggerSpec

class SlackConnector(Connector):
    key = "slack"
    display_name = "Slack"
    
    @classmethod
    def actions(cls) -> list[ActionSpec]:
        return [
            ActionSpec(
                name="post_message",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "text": {"type": "string"},
                    },
                },
                idempotent=True
            )
        ]
    
    @classmethod
    def triggers(cls) -> list[TriggerSpec]:
        return [
            TriggerSpec(name="message_created", verification_method="hmac")
        ]
    
    def execute_action(self, action: str, input_data: dict) -> Any:
        if action == "post_message":
            return self._post_message(input_data)
        raise AutomateError(ErrorCodes.INVALID_ARGUMENT, f"Unknown action: {action}")
    
    def verify_webhook(self, headers: dict, raw_body: bytes) -> bool:
        # Signature verification
        pass
```

---

## Admin Base Classes

- **Stability**: **Stable**
- **Purpose**: Reusable admin components with sensible defaults.
- **Interface**: `automate_core.base.admin`

### Base Classes

| Class | Purpose | Key Features |
|-------|---------|--------------|
| `BaseModelAdmin` | Base for all admins | Timestamps, utilities, pagination |
| `TenantScopedAdmin` | Multi-tenant filtering | Auto-filter by tenant_id |
| `AuditableModelAdmin` | Audit trail | Logs all changes |
| `ImportExportBaseAdmin` | CSV/JSON import/export | Export actions |
| `SoftDeleteAdmin` | Soft-delete support | Restore action |
| `InlineBaseAdmin` | Tabular inlines | Sensible defaults |
| `StackedInlineBaseAdmin` | Stacked inlines | Sensible defaults |

### Mixins

| Mixin | Purpose |
|-------|---------|
| `ExportMixin` | Add export actions (CSV, JSON) |
| `BulkActionsMixin` | Bulk enable/disable/status |
| `AuditMixin` | Audit logging |
| `SearchMixin` | Advanced search lookups |
| `FilterMixin` | Auto-generate filters |
| `PermissionMixin` | Object-level permissions |

### Override Points

```python
from automate_core.base.admin import BaseModelAdmin

@admin.register(MyModel)
class MyModelAdmin(BaseModelAdmin):
    # Override list display
    def get_list_display(self, request):
        display = super().get_list_display(request)
        return ['custom_field'] + display
    
    # Override queryset
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(owner=request.user)
        return qs
    
    # Override readonly fields
    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if obj and obj.is_locked:
            readonly = readonly + ['name', 'config']
        return readonly
```

---

## API Base Classes

- **Stability**: **Stable**
- **Purpose**: Reusable API components with authentication, permissions, throttling.
- **Interface**: `automate_api.v1.base`

### Base Classes

| Class | Purpose |
|-------|---------|
| `BaseAPIView` | Single-endpoint views |
| `BaseViewSet` | ViewSet operations |
| `BaseModelViewSet` | Full CRUD |
| `BaseReadOnlyViewSet` | Read-only resources |

### Mixins

| Mixin | Purpose |
|-------|---------|
| `CORSMixin` | CORS headers |
| `TenantFilterMixin` | Filter by tenant |
| `RateLimitMixin` | Custom rate limiting |
| `PaginationMixin` | Cursor/offset pagination |

### Override Points

```python
from automate_api.v1.base import BaseViewSet, TenantFilterMixin

class MyViewSet(TenantFilterMixin, BaseViewSet):
    tenant_field = 'organization_id'
    
    def get_permissions(self):
        """Dynamic permissions based on action."""
        if self.action == 'destroy':
            return [IsAdminUser()]
        return super().get_permissions()
    
    def get_throttles(self):
        """Custom throttling."""
        if self.action == 'create':
            return [CreateThrottle()]
        return super().get_throttles()
```

---

## Outbox Pattern

- **Stability**: **Stable**
- **Purpose**: Reliable async processing with transactional guarantees.
- **Interface**: `automate_core.outbox`

### Components

| Component | Purpose |
|-----------|---------|
| `OutboxItem` | Model storing work items |
| `SkipLockedClaimOutboxStore` | High-performance claiming (PostgreSQL) |
| `OptimisticClaimOutboxStore` | SQLite-compatible claiming |
| `OutboxReaper` | Recovery of stuck items |

### Usage

```python
from automate_core.outbox.store import SkipLockedClaimOutboxStore
from automate_core.outbox.reaper import OutboxReaper

# Claim items for processing
store = SkipLockedClaimOutboxStore(lease_seconds=300)
items = store.claim_batch("worker-1", limit=10)

for item in items:
    try:
        process(item)
        store.mark_success(item.id, "worker-1")
    except TransientError:
        store.mark_retry(item.id, "worker-1", next_attempt, "TRANSIENT")
    except PermanentError:
        store.mark_failed(item.id, "worker-1", "PERMANENT")

# Recover stuck items (run periodically)
reaper = OutboxReaper(stale_threshold_seconds=600)
reaped_count = reaper.reap_stale_items()
```

See [Outbox Pattern Reference](outbox-pattern.md) for detailed documentation.

---

## Signal Handlers

- **Stability**: **Stable**
- **Purpose**: React to workflow and execution events.
- **Interface**: Django signals

### Available Signals

```python
from automate.signals import (
    workflow_started,
    workflow_completed,
    workflow_failed,
    step_started,
    step_completed,
    step_failed,
    event_received,
)

# Connect handler
@receiver(workflow_completed)
def on_workflow_complete(sender, execution, **kwargs):
    send_notification(execution.owner, f"Workflow {execution.name} completed")

@receiver(step_failed)
def on_step_failure(sender, step, error, **kwargs):
    log_to_sentry(error, extra={'step_id': step.id})
```

---

## Template System

- **Stability**: **Stable**
- **Purpose**: Jinja2 templates for dynamic step inputs.
- **Interface**: `automate.templates`

### Template Context

```python
# Available in all templates
{
    "event": {
        "payload": {...},
        "type": "webhook",
        "source": "stripe",
    },
    "execution": {
        "id": "uuid",
        "name": "My Workflow",
    },
    "steps": {
        "step_1": {"output": {...}},  # Previous step outputs
    },
    "secrets": SecretResolver,  # $secret:KEY → resolved value
    "env": EnvironmentResolver,  # $env:VAR → env value
}
```

### Custom Filters

```python
# In your app's apps.py
from automate.templates import register_filter

@register_filter('format_currency')
def format_currency(value, currency='USD'):
    return f"{currency} {value:,.2f}"
```

### Template Usage

```jinja
{# In workflow step inputs #}
{
  "channel": "{{ event.payload.channel_id }}",
  "message": "Order total: {{ steps.calculate.output.total | format_currency('EUR') }}"
}
```

---

## Compatibility

All extension points maintain:

- **Django**: 4.2 (LTS), 5.0+
- **Python**: 3.10, 3.11, 3.12
- **DRF**: 3.14+

## See Also

- [Customization Guide](../guides/customization.md)
- [Admin Reference](admin.md)
- [API Base Classes](api-base-classes.md)
- [Outbox Pattern](outbox-pattern.md)

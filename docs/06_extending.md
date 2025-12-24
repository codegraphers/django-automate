# Extending Django Automate

The platform is designed as a modular core. Almost every component (Connectors, Secrets, LLMs) is a plugin.

## 1. Plugin Registry

We use Python `entry_points` to discover plugins.

**`pyproject.toml`**:
```toml
[project.entry-points."django_automate.connectors"]
my_erp = "my_app.adapters:MyERPAdapter"

[project.entry-points."django_automate.secrets.backends"]
vault = "my_app.secrets:HashiCorpVaultBackend"
```

## 2. Core Contracts

### Connectors (`ConnectorAdapter`)
Located in `automate_connectors.adapters.base`.

```python
class ConnectorAdapter(ABC):
    code: str  # Unique identifier
    name: str  # Human readable label
    
    @abstractmethod
    def execute(self, action: str, params: dict, context: dict) -> Any:
        """
        Execute the side effect.
        Must raise ConnectorError on failure.
        """
        
    def validate_config(self, config: dict):
        """Optional: Validate setup configuration."""
```

### Secrets (`SecretsBackend`)
Located in `automate_governance.secrets.interfaces`.

```python
class SecretsBackend(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> str:
        """
        Return the raw secret value.
        Raise SecretNotFoundError if missing.
        """
```

### LLM Providers (`LLMProvider`)
Located in `automate_llm.providers.base`.

```python
class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list, options: dict) -> str:
        """
        Synchronous chat completion.
        """
        
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token usage."""
```

## 3. Testing Your Plugins

We ship with **Contract Tests** to ensure your plugin behaves correctly.

**Testing a Connector**:
```python
from automate_testing.contracts import ConnectorContractTest
from my_app.adapters import MyERPAdapter

class TestMyERP(ConnectorContractTest):
    adapter_cls = MyERPAdapter
    
    def test_execute_success(self):
        # Your specific test logic
        pass
```

## 4. Internals Walkthrough

### Code Path: Webhook Ingestion
1.  **View**: `WebhookView` verifies signature.
2.  **Ingestor**: `EventIngestor.ingest()` wraps creation in a transaction.
3.  **Outbox**: An `Event` row and an `OutboxJob` row are inserted atomically.
4.  **Response**: Returns `202 Accepted` + `trace_id`.

### Code Path: The Worker Loop
1.  **Claim**: `OutboxStore.claim_batch(limit=10)` runs `SELECT ... FOR UPDATE SKIP LOCKED`.
2.  **Dispatch**: Logic is handed to `ExecutionEngine`.
3.  **Match**: `RuleEngine` finds active Workflows for the Event.
4.  **Run**: `ExecutionRun` created.
    *   Iterates steps.
    *   Resolves inputs (Jinja2).
    *    Calls `Connector.execute()`.
5.  **Commit**: Updates `OutboxJob` status to `COMPLETED`.

# Reference

## 1. Configuration (`settings.py`)

All configuration lives in the `DJANGO_AUTOMATE` dictionary.

### Core & Runtime
| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `ENABLED` | `bool` | `True` | Master kill-switch for the automation system. |
| `WORKER_MODE` | `str` | `"thread"` | `"thread"`, `"process"`, or `"synchronous"` (dev). |
| `EXECUTION.timeout_seconds` | `int` | `60` | Max duration for a single step execution. |
| `EXECUTION.max_retries` | `int` | `3` | Default retry count for transient failures. |
| `EXECUTION.batch_size` | `int` | `10` | Number of items `automate_worker` claims at once. |

### Policies & Governance
| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `POLICY.allow_ssrf` | `bool` | `False` | If False, blocks HTTP calls to private IPs (e.g. `10.0.0.0/8`). |
| `POLICY.connector_allowlist` | `list` | `["*"]` | List of allowed Connector codes. |
| `POLICY.llm_budget_daily` | `float`| `10.00`| Hard cap on LLM spend per day (USD). |

### Secrets
| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SECRETS.backend` | `str` | `"env"` | `"env"`, `"db"`, or dotted path to custom backend. |
| `SECRETS.prefix` | `str` | `"AUTOMATE_"` | Prefix for environment variable discovery. |

### Observability
| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `LOGGING_SCHEMA` | `str` | `"ecs"` | `"ecs"` (Elastic) or `"simple"`. |
| `METRICS_EXPORT` | `bool` | `False` | Enable Prometheus metrics endpoint. |

---

## 2. Python API Reference

Stable surface for integrating Automate into your Python code.

### Core Runtime
```python
from automate.runtime import emit_event, run_workflow

def emit_event(type: str, payload: dict, dedupe_key: str = None) -> str:
    """
    Ingest an event into the Outbox. 
    Returns: Event ID (UUID).
    """

def run_workflow(workflow_slug: str, payload: dict):
    """
    Directly invoke a named workflow (Bypasses Rules Engine).
    """
```

### Rules Engine
```python
from automate.rules import evaluate, explain

def evaluate(rule_spec: dict, context: dict) -> bool:
    """Returns True if context matches rules."""

def explain(rule_spec: dict, context: dict) -> dict:
    """Returns a tree showing exactly which conditions passed/failed."""
```

### Secrets & Redaction
```python
from automate.secrets import resolve, redact

def resolve(ref: str) -> str:
    """Resolves a $secret:REF string."""

def redact(data: Any) -> Any:
    """Recursively redacts sensitive keys from a dictionary."""
```

---

## 3. Data Model Reference

### `Event`
*   **Purpose**: Immutable log of inputs.
*   **Fields**: `id` (UUID), `type` (Index), `payload` (JSONB), `source` (String).
*   **Retention**: High volume. Recommend partitioning by month.

### `WorkflowVersion`
*   **Purpose**: Immutable snapshot of logic.
*   **Fields**: `workflow_id` (FK), `trigger_spec`, `steps` (JSONB), `version_num`.
*   **Note**: Executions FK to this, not the parent Workflow.

### `OutboxJob`
*   **Purpose**: Reliability queue.
*   **Fields**: `status` (PENDING, CLAIMED, COMPLETED), `lease_expires_at`, `attempts`.
*   **Indexes**: `(status, id)` for claim queries.

### `ExecutionRun`
*   **Purpose**: State machine tracker.
*   **Fields**: `trace_id` (Index), `status`, `outputs` (JSONB - Redacted).

### `AuditLogEntry`
*   **Purpose**: Compliance & Security history.
*   **Fields**: `actor`, `action`, `resource`, `details`.
*   **Security**: `details` is strictly redacted before write.

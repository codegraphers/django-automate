# Python API Reference

Complete reference for the Django Automate Python API.

## Table of Contents

1. [Runtime Module](#runtime-module)
2. [Events Module](#events-module)
3. [Rules Module](#rules-module)
4. [Secrets Module](#secrets-module)
5. [Connectors Module](#connectors-module)
6. [LLM Module](#llm-module)
7. [RAG Module](#rag-module)
8. [Outbox Module](#outbox-module)

---

## Runtime Module

**Import:** `from automate.runtime import Runtime`

### Runtime Class

The core execution engine for running workflows.

```python
from automate.runtime import Runtime

runtime = Runtime()
runtime.run_execution(execution_id="550e8400-e29b-41d4-a716-446655440000")
```

#### `run_execution(execution_id: str) -> None`

Execute a workflow by execution ID.

**Parameters:**
- `execution_id`: UUID of the execution to run

**Behavior:**
- Loads the execution and associated workflow
- Executes each step in the workflow graph
- Handles retries with exponential backoff
- Updates execution status (RUNNING → SUCCESS/FAILED)

**Raises:**
- `Execution.DoesNotExist`: If execution not found

**Example:**
```python
from automate.runtime import Runtime
from automate.models import Execution

# Create an execution
execution = Execution.objects.create(
    automation=automation,
    context={"order_id": "ORD-123"}
)

# Run it
runtime = Runtime()
runtime.run_execution(execution.id)

# Check result
execution.refresh_from_db()
print(f"Status: {execution.status}")  # SUCCESS or FAILED
```

---

## Events Module

**Import:** `from automate.events import emit_event, run_workflow`

### `emit_event(type: str, payload: dict, dedupe_key: str = None) -> str`

Ingest an event into the outbox for processing.

**Parameters:**
- `type`: Event type identifier (e.g., "order.created")
- `payload`: Event data dictionary
- `dedupe_key`: Optional deduplication key (prevents duplicate processing)

**Returns:** Event UUID string

**Example:**
```python
from automate.events import emit_event

# Simple event
event_id = emit_event(
    type="order.created",
    payload={
        "order_id": "ORD-123",
        "amount": 99.99,
        "customer_email": "john@example.com"
    }
)
print(f"Event {event_id} queued for processing")

# With deduplication (idempotent)
event_id = emit_event(
    type="payment.received",
    payload={"payment_id": "PAY-456"},
    dedupe_key="payment-PAY-456"  # Won't create duplicate if called again
)
```

### `run_workflow(workflow_slug: str, payload: dict) -> str`

Directly execute a workflow, bypassing the rule engine.

**Parameters:**
- `workflow_slug`: Slug identifier of the workflow
- `payload`: Input data for the workflow

**Returns:** Execution UUID string

**Example:**
```python
from automate.events import run_workflow

# Run workflow directly
execution_id = run_workflow(
    workflow_slug="send-welcome-email",
    payload={
        "user_id": "USR-123",
        "email": "newuser@example.com",
        "name": "John Doe"
    }
)
print(f"Started execution: {execution_id}")
```

---

## Rules Module

**Import:** `from automate.rules import evaluate, compile_rule`

### `evaluate(rule_spec: dict, context: dict) -> bool`

Evaluate a JSONLogic rule against a context.

**Parameters:**
- `rule_spec`: JSONLogic rule specification
- `context`: Data context for evaluation

**Returns:** Boolean result of rule evaluation

**Example:**
```python
from automate.rules import evaluate

# Simple comparison
result = evaluate(
    rule_spec={">=": [{"var": "amount"}, 100]},
    context={"amount": 150}
)
print(result)  # True

# Complex rule with AND/OR
rule = {
    "and": [
        {"==": [{"var": "status"}, "active"]},
        {"or": [
            {">": [{"var": "amount"}, 1000]},
            {"==": [{"var": "priority"}, "high"]}
        ]}
    ]
}
context = {"status": "active", "amount": 500, "priority": "high"}
result = evaluate(rule, context)
print(result)  # True
```

### `compile_rule(rule_spec: dict) -> CompiledRule`

Pre-compile a rule for repeated evaluation.

**Parameters:**
- `rule_spec`: JSONLogic rule specification

**Returns:** CompiledRule object with `evaluate(context)` method

**Example:**
```python
from automate.rules import compile_rule

# Compile once
rule = compile_rule({">=": [{"var": "score"}, 80]})

# Evaluate many times
for student in students:
    if rule.evaluate({"score": student.score}):
        print(f"{student.name} passed!")
```

### Supported Operations

| Operation | Example | Description |
|-----------|---------|-------------|
| `==` | `{"==": [{"var": "a"}, 1]}` | Equality |
| `!=` | `{"!=": [{"var": "a"}, 1]}` | Inequality |
| `>`, `>=`, `<`, `<=` | `{">": [{"var": "a"}, 10]}` | Comparison |
| `and` | `{"and": [...]}` | Logical AND |
| `or` | `{"or": [...]}` | Logical OR |
| `!` | `{"!": {...}}` | Logical NOT |
| `in` | `{"in": ["a", {"var": "list"}]}` | Contains |
| `var` | `{"var": "path.to.value"}` | Variable access |
| `if` | `{"if": [cond, then, else]}` | Conditional |

---

## Secrets Module

**Import:** `from automate.secrets import resolve, SecretRef`

### `resolve(ref: str) -> str`

Resolve a secret reference to its value.

**Parameters:**
- `ref`: Secret reference string (e.g., `$secret:API_KEY`)

**Returns:** Decrypted secret value

**Raises:**
- `SecretNotFoundError`: If secret doesn't exist
- `SecretAccessDenied`: If access is not permitted

**Example:**
```python
from automate.secrets import resolve

# Resolve a secret
api_key = resolve("$secret:STRIPE_API_KEY")

# Use in code
import stripe
stripe.api_key = api_key
```

### `SecretRef` Class

Type-safe secret reference for configuration.

```python
from automate.secrets import SecretRef

class MyConfig:
    api_key: SecretRef = SecretRef("$secret:API_KEY")
    
# In Pydantic models
from pydantic import BaseModel

class ConnectorConfig(BaseModel):
    api_key: SecretRef
    
    class Config:
        arbitrary_types_allowed = True
```

### Secret Reference Formats

| Format | Example | Description |
|--------|---------|-------------|
| `$secret:KEY` | `$secret:API_KEY` | Database-stored secret |
| `$env:VAR` | `$env:DATABASE_URL` | Environment variable |
| `$vault:path` | `$vault:secret/api` | HashiCorp Vault |

---

## Connectors Module

**Import:** `from automate_connectors import Connector, registry`

### Connector Base Class

```python
from automate_connectors.base import Connector, ActionSpec, TriggerSpec

class MyConnector(Connector):
    key = "my_connector"
    display_name = "My Connector"
    
    @classmethod
    def actions(cls) -> list[ActionSpec]:
        return [
            ActionSpec(
                name="send_message",
                input_schema={"type": "object", "properties": {...}},
                idempotent=True
            )
        ]
    
    def execute_action(self, action: str, input_data: dict) -> dict:
        if action == "send_message":
            return self._send_message(input_data)
        raise ValueError(f"Unknown action: {action}")
    
    def normalize_error(self, exc: Exception) -> Exception:
        return AutomateError(ErrorCodes.INTERNAL, str(exc))
```

### Registry

```python
from automate_connectors.registry import registry

# Get a connector
connector_cls = registry.get_connector("slack")
connector = connector_cls(config={...}, ctx=context)

# List all connectors
for key in registry.list_connectors():
    print(key)

# Register a connector
registry.register("my_connector", MyConnector)
```

---

## LLM Module

**Import:** `from automate_llm import chat, count_tokens, get_provider`

### `chat(messages: list[dict], **kwargs) -> str`

Send a chat completion request to the configured LLM.

**Parameters:**
- `messages`: List of message dictionaries with `role` and `content`
- `**kwargs`: Provider-specific options (model, temperature, etc.)

**Returns:** Generated text response

**Example:**
```python
from automate_llm import chat

response = chat([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
])
print(response)  # "The capital of France is Paris."

# With options
response = chat(
    messages=[{"role": "user", "content": "Write a haiku."}],
    model="gpt-4",
    temperature=0.9,
    max_tokens=100
)
```

### `count_tokens(text: str, model: str = None) -> int`

Estimate token count for text.

**Parameters:**
- `text`: Input text
- `model`: Optional model name for accurate counting

**Returns:** Estimated token count

**Example:**
```python
from automate_llm import count_tokens

tokens = count_tokens("Hello, world!")
print(f"Text uses approximately {tokens} tokens")
```

### `get_provider(name: str) -> LLMProvider`

Get an LLM provider instance.

**Parameters:**
- `name`: Provider name (openai, anthropic, etc.)

**Returns:** LLMProvider instance

**Example:**
```python
from automate_llm import get_provider

provider = get_provider("openai")
response = provider.chat([
    {"role": "user", "content": "Hello!"}
])
```

---

## RAG Module

**Import:** `from rag import query, index_documents`

### `query(endpoint: str, query_text: str, **kwargs) -> list[dict]`

Execute a RAG query.

**Parameters:**
- `endpoint`: RAG endpoint slug
- `query_text`: Natural language query
- `top_k`: Number of results (default: 5)
- `filters`: Optional metadata filters

**Returns:** List of matching documents with scores

**Example:**
```python
from rag import query

results = query(
    endpoint="support-docs",
    query_text="How do I reset my password?",
    top_k=3,
    filters={"category": "authentication"}
)

for doc in results:
    print(f"Score: {doc['score']:.2f}")
    print(f"Content: {doc['content'][:100]}...")
```

### `index_documents(endpoint: str, documents: list[dict]) -> int`

Index documents into a RAG endpoint.

**Parameters:**
- `endpoint`: RAG endpoint slug
- `documents`: List of document dictionaries

**Returns:** Number of documents indexed

**Example:**
```python
from rag import index_documents

count = index_documents(
    endpoint="support-docs",
    documents=[
        {
            "id": "doc-001",
            "content": "To reset your password, go to Settings...",
            "metadata": {"category": "authentication", "author": "admin"}
        },
        {
            "id": "doc-002",
            "content": "Two-factor authentication adds an extra layer...",
            "metadata": {"category": "security"}
        }
    ]
)
print(f"Indexed {count} documents")
```

---

## Outbox Module

**Import:** `from automate_core.outbox import OutboxStore, OutboxReaper`

### OutboxStore

Claim and process outbox items.

```python
from automate_core.outbox.store import SkipLockedClaimOutboxStore

store = SkipLockedClaimOutboxStore(lease_seconds=300)

# Claim items
items = store.claim_batch("worker-1", limit=10)

for item in items:
    try:
        process(item)
        store.mark_success(item.id, "worker-1")
    except TransientError as e:
        store.mark_retry(item.id, "worker-1", next_attempt, str(e))
    except PermanentError as e:
        store.mark_failed(item.id, "worker-1", str(e))
```

### OutboxReaper

Recover stuck items.

```python
from automate_core.outbox.reaper import OutboxReaper

reaper = OutboxReaper(stale_threshold_seconds=600)
reaped = reaper.reap_stale_items()
print(f"Recovered {reaped} stuck items")
```

See [Outbox Pattern Reference](../outbox-pattern.md) for detailed documentation.

---

## Type Annotations

All public APIs include full type annotations:

```python
from typing import Any

def emit_event(
    type: str,
    payload: dict[str, Any],
    dedupe_key: str | None = None
) -> str: ...

def evaluate(
    rule_spec: dict[str, Any],
    context: dict[str, Any]
) -> bool: ...
```

## Async Support

Most APIs have async variants:

```python
from automate_llm import achat

response = await achat([
    {"role": "user", "content": "Hello!"}
])
```

## See Also

- [REST API Reference](../rest-api/index.md)
- [Extension Points](../extension-points.md)
- [Customization Guide](../../guides/customization.md)

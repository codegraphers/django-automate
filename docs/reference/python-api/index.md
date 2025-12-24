# Python API Reference

Stable public API surface for `django-automate`.

## Runtime

### `emit_event`
```python
def emit_event(type: str, payload: dict, dedupe_key: str = None) -> str:
```
Ingests an event into the Outbox. Returns the Event UUID.

### `run_workflow`
```python
def run_workflow(workflow_slug: str, payload: dict) -> str:
```
Directly bypasses the rule engine and executes a named workflow.

## Rules

### `evaluate`
```python
def evaluate(rule_spec: dict, context: dict) -> bool:
```
Evaluates a JSONLogic rule against a context.

## Secrets

### `resolve`
```python
def resolve(ref: str) -> str:
```
Resolves a `$secret:` reference string. This calls the configured backend.

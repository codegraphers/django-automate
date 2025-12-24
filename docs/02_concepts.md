# Core Concepts

Understanding the mental model of Django Automate: **Event → Rule → Workflow → Execution**.

## The Automation Pipeline

1.  **Event**: Something happens (Signal, Webhook, Schedule). It is immutable and contains a payload (e.g., JSON body, model instance data).
2.  **Rule Match**: The **Rules Engine** evaluates the event against active **RuleSpecs**. Complex logic (JSONLogic) determines if a workflow should trigger.
3.  **Workflow Version**: Workflows are versioned. An execution is tied to a specific snapshot of a workflow definition, ensuring consistency even if the workflow is edited mid-run.
4.  **Execution Run**: An instance of a workflow running for a specific event. Contains a globally unique `trace_id`.
5.  **Steps**: Individual units of work (Actions). Steps are executed sequentially (or parallel/fan-out in advanced configs).

## Key Guarantees

### Idempotency & "Once-ish" Execution
The system uses `idempotency_keys` for every execution. If the same webhook payload arrives twice (with the same ID), the second one is practically ignored or attached to the existing run, preventing duplicate side effects (like charging a card twice).

### Reliability (The Outbox Pattern)
We do not execute side effects immediately in the HTTP request loop.
1.  **Commit Phase**: The event and intent-to-run are saved to the **Outbox** (DB).
2.  **Async Phase**: A reliable worker (Celery or Management Command) claims the outbox item via a locking mechanism (`SKIP LOCKED` on Postgres).
3.  **Retry Phase**: If a step fails, it is retried with exponential backoff based on the policy. Dead Letter Queues (DLQ) capture permanent failures.

## Security Model

### SecretRefs
**NEVER** store API keys in workflow definitions. Use `SecretRef`:
```json
{
    "api_key": {"$secret": "STRIPE_LIVE_KEY"}
}
```
The **Governance Layer** resolves this at runtime using configured Backends (Env, Vault, Encrypted DB).

### Redaction
The **Audit Log** automatically redacts values that look like sensitive keys or PII before saving to the database, ensuring your logs don't leak secrets.

### Policy Engine
Administrators can define global policies:
*   **Budget**: Max $5.00/day on LLM calls.
*   **Rate Limits**: Max 100 webhooks/minute per tenant.
*   **Allowlists**: Only allow HTTP calls to `*.stripe.com`.

# Welcome to Django Automate

**Django Automate** separates the **Control Plane** (defining *what* should happen) from the **Execution Plane** (ensuring it *actually* happens).

## Core Guarantees
*   **Idempotency Intent**: We use `idempotency_keys` to ensure that even if an event is replayed, the side-effects happen "practically once". policy.
*   **Audit**: Every action is effectively immutable and logged.
*   **Policy & Governance**: Secret redaction and budget limits are enforced at the runtime level, not just the UI level.
*   **Traceability**: A `trace_id` flows from the inbound webhook -> event -> rule -> workflow -> connector -> external system.

---

## Conventions

### Versioning & Compatibility
*   **SemVer**: We follow Semantic Versioning `MAJOR.MINOR.PATCH`.
*   **Python**: 3.10, 3.11, 3.12+
*   **Django**: 4.2 (LTS), 5.0+
*   **DRF**: 3.14+
*   **Databases**:
    *   **Postgres**: Recommended (Required for `SKIP LOCKED` high-throughput).
    *   **MySQL 8+**: Supported (No JSON index optimizations).
    *   **SQLite**: Dev/Test only.

### Glossary

| Term | Definition |
| :--- | :--- |
| **Event** | An immutable record of a signal, webhook, or schedule tick. Contains a raw payload. |
| **RuleSpec** | A JSON-based logic definition (predicates) used to match Events to Workflows. |
| **WorkflowVersion** | An immutable snapshot of a workflow definition. Executions are pinned to a specific version. |
| **OutboxJob** | A transactional record representing the *intent* to process an Event. Guarantees reliability. |
| **ExecutionRun** | The state machine instance processing a WorkflowVersion for a specific Event. |
| **StepRun** | A single unit of work within a Run (e.g., "Post to Slack"). |
| **TraceId** | A UUID connecting the chain of events across distributed systems. |
| **SecretRef** | A pointer string (e.g., `$secret:STRIPE_KEY`) resolved at runtime to a secure value. |

### Error Format Contract
All API errors follow the `NormalizedError` shape:
```json
{
  "code": "resource_not_found",
  "message": "Workflow with ID 123 does not exist.",
  "details": { "id": "123" },
  "trace_id": "aa-bb-cc-dd"
}
```

### Data Redaction
*   **Safe Payloads**: Logs and UI displays automatically redact values mirroring keys like `password`, `token`, `key`, `authorization`.
*   **Raw Payloads**: Accessing the raw, unredacted payload requires specific `view_raw_payload` permission in Admin.

### Pagination
Cursor-based pagination is used for high-volume endpoints (Events, Runs).
`?cursor=cD0yMDIz&limit=50`

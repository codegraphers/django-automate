# Data Models Reference

## Event (`automate_core.Event`)
*   **id**: UUID (PK)
*   **type**: String (Indexed) - The event designator e.g. `stripe.charge`
*   **payload**: JSONB - The raw input data.
*   **received_at**: DateTime

## Workflow (`automate_core.Workflow`)
*   **name**: String
*   **is_active**: Boolean
*   **versions**: One-to-Many to `WorkflowVersion`

## ExecutionRun (`automate_core.ExecutionRun`)
*   **trace_id**: UUID (Indexed)
*   **status**: Enum (PENDING, RUNNING, COMPLETED, FAILED)
*   **workflow_version**: FK
*   **event**: FK

## AuditLogEntry (`automate_observability.AuditLogEntry`)
*   **actor**: String
*   **action**: String
*   **resource**: String
*   **details**: JSONB (Redacted)

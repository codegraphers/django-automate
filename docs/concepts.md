# Core Concepts

## The Pipeline

Data flows through the system in these stages:

1. **Ingestion**: An external system or code sends an `Event` payload.
2. **Outbox**: The event is saved transactionally with an `Outbox` entry (`PENDING`).
3. **Dispatch**: The `Dispatcher` process picks up pending items, resolves matching `Automations`, creates `Execution` records, and marks the Outbox item `PROCESSED`.
4. **Execution**: The `Runtime` executes the steps defined in the `Workflow` graph.

## Key Models

- **Event**: Immutable record of something happening (`type`, `payload`).
- **Outbox**: Queue state for an Event (`status`, `attempts`, `next_attempt_at`).
- **Automation**: Container for Triggers and Workflows.
- **Workflow**: Versioned graph of steps.
- **Execution**: A single run of an Automation for an Event.
- **ExecutionStep**: Log of a single step's input/output.

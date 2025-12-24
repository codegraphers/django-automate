# Documentation Style Guide

This guide defines how to write documentation for **Django Automate**.

## Goals
*   **Fast Path**: Users must succeed in 10 minutes.
*   **Predictable**: Every page shares the same structure.
*   **Safe**: No secret leakage in examples or logs.
*   **Parity**: Admin Studio features must map to API equivalents.

---

## Page Template
Every non-reference page must follow this skeleton:

1.  **What you’ll build / do**
2.  **Prerequisites**
3.  **Steps**
4.  **Expected output**
5.  **Common errors / Troubleshooting**
6.  **Next steps**

## Terminology
*   **Event**: Immutable ingestion record.
*   **Trigger**: Source of events.
*   **RuleSpec**: Logic conditions.
*   **Workflow / Version**: Definition snapshots.
*   **ExecutionRun**: Instance of a workflow.
*   **OutboxJob**: Transactional queue item.
*   **SecretRef**: Configuration pointer (`$secret:KEY`).

## Code Snippets
*   Use language tags: `python`, `json`, `bash`.
*   Use stable placeholders:
    *   `SECRETREF://prod/slack/api_key`
    *   `sk_live_***`
    *   `whsec_***`

## Security & Redaction
*   **Redact**: Keys named `api_key`, `token`, `secret`.
*   **Screenshots**: Never show raw permissions or secret values.

## Admonitions
*   **Note**: Context.
*   **Tip**: Best practice.
*   **Warning**: Security/Risk.
*   **DB Capability**: SQLite vs Postgres differences.

## QA Checklist
*   [ ] No secrets visible.
*   [ ] Language tags present.
*   [ ] 2+ Internal links.
*   [ ] DB capability notes included.

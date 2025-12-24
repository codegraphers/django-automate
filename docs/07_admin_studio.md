# Admin Studio Guide

The **Studio** provides a visual interface for the Control Plane.

## Navigation Map

1.  **Automation Wizard** (`/studio/wizard/`):
    *   **Purpose**: Authoring workflows visually.
    *   **Key Features**: Drag-and-drop canvas, AI Copilot, Component Palette.
2.  **Rule Tester** (`/studio/tester/`):
    *   **Purpose**: "Unit testing" logic. Used to verify JSON rules against sample events.
    *   **Output**: An "Explain Tree" showing exactly which predicate matched or failed.
3.  **Execution Explorer** (`/studio/explorer/`):
    *   **Purpose**: Operational visibility.
    *   **Features**: Timeline view of steps, input/output inspection (redacted).
4.  **Governance**:
    *   **Stored Secrets**: Manage encrypted secrets (if DB backend used).
    *   **Audit Log**: Immutable history of all changes.

## Permissions Matrix

| Permission | Description |
| :--- | :--- |
| `automate.view_studio` | Access to the Studio dashboard. |
| `automate.publish_workflow`| Ability to create/update live workflows. |
| `automate.view_raw_payload`| **SENSITIVE**: Allows viewing unredacted JSON inputs in Explorer. |
| `automate.manage_secrets` | Ability to rotate or create stored secrets. |

## Workflow Lifecycle

1.  **Draft**: Workflows in the Wizard start as client-side drafts.
2.  **Publish**: Clicking "Publish" creates a persistent `Workflow` record and an active `WorkflowVersion`.
3.  **Archive**: Deleting a workflow sets `is_active=False` but keeps history.

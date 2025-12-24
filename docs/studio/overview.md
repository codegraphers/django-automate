# Admin Studio Overview

The **Admin Studio** (`/studio/`) is the visual control plane.

## Components

### Automation Wizard
The primary authoring tool.
*   **Drag & Drop**: Visually arrange steps.
*   **AI Copilot**: Generate workflows from text descriptions.
*   **Import**: Paste n8n-compatible JSON.

### Rule Tester
A "Unit Test" workbench for your logic.
*   **Input**: Paste a JSON event.
*   **Logic**: Paste a JSON rule.
*   **Result**: Visual tree showing pass/fail of every condition.

### Execution Explorer
The operational dashboard.
*   **Visual Timeline**: See timing of every step.
*   **Payload Inspection**: Click steps to see data (Redacted by default).
*   **Status Indicators**: Quickly find failed runs.

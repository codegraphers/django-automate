# Execution Explorer

The debugger for your automations.

## Features

### Visual Timeline
A Gantt-chart style view of step execution.
*   **Bar Length**: Duration of the step.
*   **Color**: Green (Success), Red (Fail), Gray (Skipped).

### Payload Inspection
Click any step to see:
*   **Input**: The JSON data passed to the step.
*   **Output**: The JSON data returned.
*   **State**: Variable context at that point in time.

> [!WARNING]
> **Redaction**: By default, sensitive keys are masked. You need the `can_view_raw_payloads` permission to see unmasked data.

### Reprocessing
failed runs can be replayed.
*   **Replay from Step**: Re-run just the failed step and subsequent steps.
*   **Full Replay**: Start fresh with the original event.

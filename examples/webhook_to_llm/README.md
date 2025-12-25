# Webhook to LLM Example

This example demonstrates the "Golden Path":
1.  **Trigger**: Authenticated Webhook
2.  **Workflow**: Log the event (Action)
3.  **Verification**: Poll for completion

## Prerequisites

Running stack:
```bash
make dev
```

## Run

```bash
python run.py
```

This script will:
- Seed the Automation and Workflow
- Trigger the webhook via HTTP
- Poll the database for the Job result
- Assert success

# n8n Connector

Trigger external n8n workflows via Webhook.

## Setup

1. **n8n Workflow**: Create a workflow in n8n starting with a **Webhook** node.
2. **Method**: Set method to `POST`.
3. **URL**: Copy the Production URL (e.g., `https://n8n.example.com/webhook/uuid`).

## Connection Profile

Currently, n8n does not strictly require auth for public webhooks, but you can add Header Auth.

- **Slug**: `n8n-main`
- **Connector**: `n8n`
- **Secrets**:
  ```json
  {
    "api_key": "env://N8N_API_KEY"
  }
  ```

## Usage

In your Workflow, specify the `webhook_id` (the last part of the URL):

```json
{
  "id": "process-in-n8n",
  "type": "n8n",
  "config": {
    "webhook_id": "uuid-from-n8n-url",
    "payload": {
       "data": "{{ event.payload }}"
    }
  }
}
```

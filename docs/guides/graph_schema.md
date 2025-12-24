# Graph Schema

Workflow graphs are defined in JSON.

## Structure

```json
{
  "nodes": [
    {
      "id": "STEP_ID",
      "type": "CONNECTOR_SLUG",
      "config": { ... },
      "next": ["NEXT_STEP_ID"]
    }
  ],
  "edges": [] // Currently unused in MVP (Implicit via 'next')
}
```

## Node Types

- **`logging`**: Logs a message.
    - `config`: `{"msg": "template string"}`
- **`slack`**: Posts to Slack.
    - `config`: `{"channel": "#name", "text": "template string"}`
- **`n8n`**: Triggers n8n webhook.
    - `config`: `{"webhook_id": "uuid", "payload": {}}`
- **`webhook`**: Generic HTTP Request.
    - `config`: `{"url": "...", "method": "POST", "headers": {}, "json": {}}`

## Templating
All config values support Jinja2 templating.
- `{{ event.payload }}`: The raw event data.
- `{{ event.source }}`: Event source.

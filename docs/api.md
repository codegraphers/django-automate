# API Reference

## Endpoints

### Manual Trigger
`POST /automate/manual`

Trigger an automation manually.

**Payload:**
```json
{
  "event": "event-slug",
  "payload": { "foo": "bar" }
}
```

### Zapier Triggers
`GET /automate/zapier/triggers`

List available triggers for Zapier integration.

## Swagger UI

For interactive API documentation, visit:
[http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)

# API Reference

Django Automate exposes a versioned REST API at `/api/v1/`.

---

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/v1/workflows/` | Workflow management |
| `/api/v1/executions/` | Execution tracking |
| `/api/v1/jobs/` | Job queue operations |
| `/api/v1/events/` | Event ingestion |
| `/api/v1/triggers/` | Trigger configuration |
| `/api/v1/connectors/` | Connector management |

---

## Authentication

The API supports multiple authentication schemes:

```python
# Token authentication
Authorization: Token <your-token>

# JWT authentication
Authorization: Bearer <jwt-token>

# Session (for admin users)
Cookie: sessionid=<session-id>
```

Configure in `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

---

## Correlation ID

All requests support correlation ID propagation for distributed tracing:

```http
X-Correlation-ID: <uuid>
```

If not provided, a new UUID is generated and returned in the response.

---

## OpenAPI Schema

Interactive documentation available at:

- **Swagger UI**: `/api/docs/`
- **OpenAPI Schema**: `/api/schema/`

```bash
# Download schema
curl https://your-server/api/schema/ -o openapi.yaml
```

---

## Rate Limiting

Default rate limits (configurable via settings):

| Scope | Limit |
|-------|-------|
| Anonymous | 100/hour |
| Authenticated | 1000/hour |
| Burst | 10/second |

---

## Error Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input",
    "details": {
      "field": ["This field is required."]
    }
  },
  "correlation_id": "abc123"
}
```

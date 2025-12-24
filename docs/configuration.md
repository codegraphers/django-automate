# Configuration

Configure behavior via `settings.py`.

## Core

| Setting | Default | Description |
|:---|:---|:---|
| `AUTOMATE_MAX_RETRIES` | `3` | Max attempts before marking execution DEAD. |
| `AUTOMATE_ALLOW_RAW_SECRETS` | `False` | **DEV ONLY**. If `True`, allows secrets in input payloads. |

## Webhooks (SSRF Protection)

| Setting | Default | Description |
|:---|:---|:---|
| `AUTOMATE_WEBHOOK_ALLOWED_HOSTS` | `[]` | List of allowed hostnames/IPs. Empty = All (except local). |
| `AUTOMATE_WEBHOOK_ALLOW_LOCAL` | `False` | If `True`, allows localhost/private IP connections. |

## Redis (Optional)

Currently used for throttling and lock coordination.

```python
AUTOMATE_REDIS_URL = "redis://localhost:6379/1"
```

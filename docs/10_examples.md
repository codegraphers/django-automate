# Examples & Templates

Copy-pasteable JSON templates for common workflows.

## 1. Minimal Webhook Logger
**Use Case**: Debugging - log every incoming webhook.

```json
{
  "name": "Debug Webhooks",
  "trigger": { "type": "webhook", "config": { "path": "*" } },
  "steps": [
    {
      "action": "core.log",
      "config": {
        "level": "INFO",
        "message": "Received: {{event.payload}}"
      }
    }
  ]
}
```

## 2. Customer Tier Alert (Slack)
**Use Case**: Notify sales when a VIP customer logs in.

```json
{
  "name": "VIP Login Alert",
  "trigger": {
    "type": "signal",
    "config": { "model": "auth.Session", "signal": "create" }
  },
  "rules": {
    "==": [{ "var": "user.profile.tier" }, "VIP"]
  },
  "steps": [
    {
      "action": "slack.post_message",
      "config": {
        "channel": "#sales-vip",
        "text": "🌟 VIP User {{event.user.email}} just logged in!"
      }
    }
  ]
}
```

## 3. Daily Summary Report (Cron + LLM)
**Use Case**: summarize yesterday's errors usage.

```json
{
  "name": "Daily Error Report",
  "trigger": { "type": "schedule", "config": { "cron": "0 8 * * *" } },
  "steps": [
    {
      "id": "fetch_logs",
      "action": "db.query",
      "config": { "sql": "SELECT * FROM audit_logs WHERE status='FAILED' AND created > NOW() - INTERVAL '1 day'" }
    },
    {
      "id": "summarize",
      "action": "llm.chat",
      "config": {
        "model": "gpt-4",
        "prompt": "Summarize these errors: {{steps.fetch_logs.output}}"
      }
    },
    {
      "action": "email.send",
      "config": {
        "to": "dev-team@company.com",
        "subject": "Daily Error Summary",
        "body": "{{steps.summarize.output.text}}"
      }
    }
  ]
}
```

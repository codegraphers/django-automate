# Slack Connector

Send messages to Slack channels.

## Setup

1. **Create Slack App**: Go to [api.slack.com](https://api.slack.com/apps), enable "Incoming Webhooks" or "Bots".
2. **Scopes**: Add `chat:write`, `channels:read`.
3. **Install**: Install app to your workspace. Copy the `Bot User OAuth Token` (starts with `xoxb-`).

## Connection Profile

Create a `ConnectionProfile` in Django Admin.

- **Slug**: `slack-prod`
- **Connector**: `Slack`
- **Secrets**:
  ```json
  {
    "token": "env://SLACK_BOT_TOKEN"
  }
  ```
  *(Ensure `SLACK_BOT_TOKEN` is in your environment variables)*

## Usage

In your Workflow Graph:

```json
{
  "id": "notify",
  "type": "slack",
  "config": {
    "channel": "#general",
    "text": "Hello form Automate! Event: {{ event.payload.id }}"
  }
}
```

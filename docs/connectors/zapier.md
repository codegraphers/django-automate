# Zapier Integration

The Zapier integration works via **REST Hooks**. Zapier subscribes to our `zapier/subscribe` endpoint, and we push events to them.

## Setup

Since this is a private API integration, you would typically build a private Zapier App using the Zapier Developer Platform.

### Endpoints
Your Zapier App will need to configure:

- **Subscribe URL**: `POST /automate/zapier/subscribe`
- **Unsubscribe URL**: `DELETE /automate/zapier/unsubscribe`
- **List Triggers**: `GET /automate/zapier/triggers`

### Usage
Once your Zapier App is connected, users can create Zaps that trigger when specific Django Automate events occur (e.g. `workflow_completed`, `manual_trigger`).

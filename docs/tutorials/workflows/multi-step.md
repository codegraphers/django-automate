# Multi-Step Workflows

## 1. What you'll build
A workflow that Chains multiple actions: Webhook -> Transform -> Slack -> Email.

## 2. Prequisites
*   Completed [First Automation](../../quickstart/first-automation.md).

## 3. Steps

### Define the Workflow
```json
{
    "name": "Order Process",
    "trigger": { "type": "webhook", "config": { "path": "order" } },
    "steps": [
        {
            "id": "notify_slack",
            "action": "slack.post_message",
            "config": {
                "channel": "#orders",
                "text": "New Order: {{event.payload.id}}"
            }
        },
        {
            "id": "send_email",
            "action": "email.send",
            "config": {
                "to": "{{event.payload.customer_email}}",
                "subject": "Order Received",
                "body": "Thanks for your order!"
            }
        }
    ]
}
```

### Accessing Previous Outputs
You can verify the output of step 1 in step 2 (if it had an output).
`{{ steps.notify_slack.output.ts }}` (Slack Timestamp).

## 4. Expected Output
1.  Post to Slack.
2.  Send Email.
3.  Audit log shows 2 distinct step executions.

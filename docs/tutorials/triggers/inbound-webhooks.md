# Inbound Webhooks Tutorial

## 1. What you'll build
A workflow that triggers when an external webhook (e.g., Stripe) hits your endpoint.

## 2. Prerequisites
*   A running Django Automate instance.
*   A tool like Postman or `curl` to simulate webhooks.

## 3. Steps

### Configure Ingestion
Ensure your `urls.py` includes the API routes. The generic webhook ingestion endpoint is `POST /api/automate/webhooks/{source}/`.

### Define the Rule
We only want to trigger when the event type is `checkout.session.completed`.

```json
{
  "and": [
    { "==": [{ "var": "type" }, "checkout.session.completed"] },
    { "==": [{ "var": "data.object.payment_status" }, "paid"] }
  ]
}
```

### Add the Action
Call your internal API to provision access using the `http.post` connector.

```json
{
  "action": "http.post",
  "config": {
    "url": "http://internal-api/provision",
    "json": {
        "user_email": "{{ event.data.object.customer_email }}",
        "plan": "premium"
    }
  }
}
```

## 4. Testing
Send a POST request to `http://localhost:8000/api/automate/webhooks/stripe/`:
```json
{
    "type": "checkout.session.completed",
    "data": { "object": { "payment_status": "paid", "customer_email": "test@example.com" } }
}
```

## 5. Next Steps
*   [Secure your webhook with signatures](../../security/webhook-signatures.md)

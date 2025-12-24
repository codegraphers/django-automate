# Webhook Signature Verification

Securing inbound webhooks is critical to prevent attackers from spoofing events.

## The Mechanic
We use HMAC-SHA256. The sender (e.g. Stripe) includes a header `Stripe-Signature` containing a timestamp and a signature. We calculate the expected signature using a shared secret and compare.

## Configuration

In `settings.py`:

```python
DJANGO_AUTOMATE = {
    # ...
    "WEBHOOKS": {
        "stripe": {
            "secret": "whsec_...",
            "header": "Stripe-Signature",
            "algorithm": "hmac-sha256",
        }
    }
}
```

## How it works internally
The `WebhookIngestor` view:
1.  Looks up the secret for the source.
2.  Computes `hmac.new(secret, payload, sha256)`.
3.  Compares with the header.
4.  Rejects with `401 Unauthorized` if mismatch.

## Best Practices
*   **Rotation**: Support multiple secrets (list) during rotation.
*   **Timestamp**: Verify the timestamp is within tolerance (e.g. 5 mins) to prevent replay attacks.

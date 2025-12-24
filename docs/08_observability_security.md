# Observability & Security

## Observability

### Structured Logging
We use a JSON log formatter compatible with ECS (Elastic Common Schema).

**Schema**:
```json
{
  "@timestamp": "2023-10-01T12:00:00Z",
  "log.level": "INFO",
  "message": "Step executed successfully",
  "trace.id": "abc-123-xyz",
  "transaction.id": "run-999",
  "automate": {
    "workflow": "welcome_email",
    "step": "send_email",
    "component": "connector"
  }
}
```

### Trace Propagation
*   **Ingress**: We look for `X-Trace-Id` headers on incoming webhooks.
*   **Internal**: `trace_id` is passed to the `OutboxJob` and then to the `ExecutionRun`.
*   **Egress**: Connectors inject `X-Trace-Id` into outgoing HTTP requests (if supported), allowing end-to-end tracing across services.

### Audit Logs
Accessed via Admin. Every modification to a workflow, secret, or policy is recorded.
*   **Retention**: Rows are never deleted by the application. Configure a DB retention policy if needed.

---

## Security Deep Dive

### Threat Model: SSRF
**Risk**: Users configuring HTTP Connectors to hit internal AWS endpoints (e.g., `http://169.254.169.254/latest/meta-data`).
**Mitigation**: `POLICY.allow_ssrf` defaults to `False`. The HTTP connector resolves DNS and checks against private IP ranges before connecting.

### Threat Model: Secret Leakage
**Risk**: A user prints a secret to the logs: `{{ $secret.API_KEY }}`.
**Mitigation**:
1.  **Redaction Engine**: The `SecretResolver` registers all loaded values.
2.  **Log Filter**: A logging filter scans all distinct log messages for these known secret values and replaces them with `[REDACTED]`.

### Webhook Verification
**Pattern**:
Do not blindly trust `POST` requests.
1.  Configure `AUTOMATE_WEBHOOK_SECRETS = {"stripe": "whsec_..."}`.
2.  The `WebhookView` calculates HMAC-SHA256 signature.
3.  Requests with invalid signatures are rejected 401 before ingestion.

# Governance & Safety Layer

## 1. Secrets Management
The platform uses `SecretRef` to prevent plaintext secrets in code or database.

### Configuring Secrets
In `settings.py`:
```python
AUTOMATE = {
    "SECRETS": {
        "DEFAULT_BACKEND": "env",
        "BACKENDS": {
            "env": {"CLASS": "automate_governance.secrets.backends.EnvBackend"},
            "encrypted_db": {
                "CLASS": "automate_governance.secrets.backends.EncryptedDBBackend",
                "KMS": {"CLASS": "automate_governance.secrets.kms.DjangoSigningKMS"}
            }
        }
    }
}
```

### Usage
- **Admin**: Create a `ConnectionProfile`. In the `secrets` JSON field, use:
  ```json
  {"api_key": "secretref://env/stripe/prod/key"}
  ```
- **Code**:
  ```python
  from automate_governance.secrets.resolver import SecretResolver
  resolver = SecretResolver(...)
  secret = resolver.resolve_value("secretref://...")
  ```

## 2. Rules Engine
Safe JSONLogic evaluation for Triggers and Policies.

### Supported Operators
- `==`, `!=`, `>`, `<`, `in`, `contains`
- **Variables**: `event.*`, `ctx.*`

### Example Rule
```json
{
  "and": [
    { "==": [{ "var": "event.type" }, "order.created"] },
    { ">": [{ "var": "event.payload.amount" }, 100] }
  ]
}
```

## 3. Reliability (Outbox)
Events and Tasks are processed via the DB-backed Outbox.
- **Workers**: Run `python manage.py run_worker` (future command) or generic dispatcher.
- **Retries**: Exponential backoff (up to 15 attempts default).

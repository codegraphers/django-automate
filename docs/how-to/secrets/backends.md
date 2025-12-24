# Secrets Backends

Automate supports pluggable backends for secret resolution.

## 1. EnvBackend (Default)
Reads from process environment variables.
*   **Pros**: Fast, standard 12-factor app pattern.
*   **Cons**: Requires restart to change (usually).

```python
"SECRETS": {
    "backend": "automate_governance.secrets.backends.EnvBackend",
    "prefix": "AUTOMATE_"
}
```

## 2. EncryptedDBBackend
Stores secrets in the Postgres database, encrypted at rest using Fernet (symmetric encryption).
*   **Pros**: Rotation via Admin UI, no restarts.
*   **Cons**: Database access = Secret access (if encryption key is also on server).

## 3. HashiCorp Vault (Enterprise)
Connects to a remote Vault instance.
*   **Pros**: Centralized audit, dynamic leases.
*   **Cons**: Infrastructure complexity.

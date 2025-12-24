# Using SecretRefs

**NEVER** hardcode secrets (API keys, tokens, passwords) in your workflow definitions. Use `SecretRef` pointers.

## How it works
A `SecretRef` is a string pointer in the format `{"$secret": "KEY_NAME"}`. At runtime, the execution engine intercepts this pattern and resolves it using the configured Secrets Backend before passing it to the Connector.

## Step-by-Step

### 1. Configure the Backend
In `settings.py`, choose your backend. The default is `EnvBackend`, which reads from environment variables.

```python
DJANGO_AUTOMATE = {
    "SECRETS": {
        "backend": "automate_governance.secrets.backends.EnvBackend",
        "prefix": "AUTOMATE_", 
    }
}
```

### 2. Set the Environment Variable
Export your secret with the matching prefix.
```bash
export AUTOMATE_STRIPE_LIVE_KEY="sk_live_12345abcdef"
```

### 3. Use in Workflow
In your JSON definition or the Studio Wizard:

```json
"headers": {
    "Authorization": "Bearer {{$secret.STRIPE_LIVE_KEY}}"
}
```

> [!NOTE]
> **Security**: The resolved value "sk_live_..." is never saved to the database. It exists in memory only during the split-second execution of the step.

## Next Steps
*   [Rotate Secrets](rotation.md)
*   [Use Encrypted DB Backend](backends.md)

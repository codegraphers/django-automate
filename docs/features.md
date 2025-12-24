# Features

## Secrets Management
Django Automate uses a pluggable `SecretsBackend`. By default, `EnvSecretsBackend` is used.

- **Storage**: Secrets in `ConnectionProfile` are encrypted (simulated in MVP) and should refer to env vars via `env://MY_VAR`.
- **Resolution**: Connectors resolve these at runtime.
- **Leaking**: Inputs are redacted from logs and DB if exceptions occur.

## Connectors
Built-in connectors include:
- **Slack**: Post messages to channels.
- **Webhook**: Send HTTP requests (with SSRF protection).
- **n8n**: Trigger external n8n workflows (Backend integration).

## Operability
Use standard Django management commands:

- `automate_dispatch`: Runs the main loop.
- `automate_replay_deadletters`: Moves DEAD items back to PENDING.
- `automate_healthcheck`: Shows queue depth.

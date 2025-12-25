# Extension Points

This framework is designed to be extended. Below are the stable interfaces for plugins.

## Provider Registry

- **Name**: `ProviderRegistry`
- **Stability**: **Stable**
- **Purpose**: Discovers and loads external capabilities (LLMs, Tools).
- **Interface**: `automate_core.providers.base.BaseProvider`

### How to Register
Add your provider class path to `AUTOMATE_PROVIDERS` in settings, or use the `django_automate.providers` entrypoint in `pyproject.toml`.

### Compatibility
- Django 4.2+
- Python 3.10+

---

## Secrets Backend

- **Name**: `SecretsBackend`
- **Stability**: **Stable**
- **Purpose**: Resolves sensitive credentials at runtime.
- **Interface**: `automate.secrets_backend.SecretsBackend`

### Implementation
Override `resolve(self, key: str) -> str`.

---

## Connector

- **Name**: `Connector`
- **Stability**: **Beta**
- **Purpose**: Defines Actions and Triggers for external services.
- **Interface**: `automate_connectors.base.Connector`

# Security Threat Model

## Server-Side Request Forgery (SSRF)
**Risk**: Users configuring an HTTP Connector to access internal metadata services (e.g. AWS `169.254.169.254`).
**Mitigation**:
*   `POLICY.allow_ssrf` setting defaults to `False`.
*   The connector performs DNS resolution and checks against private IP ranges (`10.0.0.0/8`, `127.0.0.0/8`, etc.) before establishing a connection.

## Secret Leakage
**Risk**: Users accidentally logging secrets or viewing them in the UI.
**Mitigation**:
*   **SecretRef**: Secrets are not stored in the Workflow definition.
*   **Redaction**: The `SecretResolver` registers all active secrets. The logging formatter and UI serializers aggressively scrub these strings from output.

## Code Injection
**Risk**: Using `eval()` in Python.
**Mitigation**:
*   We use **JSONLogic** for rules, which is a safe, data-only constrained language.
*   We use **Jinja2 SandboxedEnvironment** for templates, preventing access to `os`, `sys`, or `__subclasses__`.

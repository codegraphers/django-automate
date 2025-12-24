# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please email security@example.com instead of opening a public issue.
We commit to responding within 48 hours.

## Key Security Features

*   **SecretRef**: No plaintext credentials in DB or logs.
*   **SSRF Protection**: All outbound requests are validated against private IP ranges.
*   **Redaction**: Logs and Admin UI automatically redact sensitive fields.

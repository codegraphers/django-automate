# Deployment Checklist

## Database
*   [ ] **Postgres**: Verify version 12+.
*   [ ] **Connections**: Ensure `max_connections` can handle `WEB_CONCURRENCY + WORKER_CONCURRENCY`.

## Workers
*   [ ] **Process Manager**: Use Supervisor or Docker to keep `python manage.py automate_worker` running.
*   [ ] **Scale**: Start with 1 worker per CPU core.

## Security
*   [ ] **Secrets**: Set `AUTOMATE_SECRET_KEY_PREFIX`.
*   [ ] **HTTPS**: Ensure all webhook callbacks use HTTPS.
*   [ ] **Allowed Hosts**: Configure `POLICY.connector_allowlist` if you want to restrict which external APIs can be called.

## Maintenance
*   [ ] **Audit Logs**: Configure a cleanup policy for `automate_audit_log` table if high volume.

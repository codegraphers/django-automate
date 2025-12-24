# Operations & Deployment

Checklist for going to production.

## Production Checklist

### 1. Database
*   [ ] **Postgres 12+**: Strongly recommended for `SKIP LOCKED` support and JSONB performance.
*   [ ] **Connections**: Ensure your connection pool (PgBouncer) handles the worker threads.

### 2. Worker Topology
*   [ ] **Process Isolation**: Run workers separately from your Web/API nodes.
*   [ ] **Scale**: Start with 1 process per CPU core. Monitor CPU and Memory.
*   [ ] **Queues**: If using Celery, configure a dedicated high-priority queue for `automate` tasks.

### 3. Security Hardening
*   [ ] **Secrets**: Ensure `AUTOMATE_SECRET_KEY_PREFIX` is set and environment variables are injected securely.
*   [ ] **SSRF**: If using generic HTTP connectors, configure the `ALLOWLIST_HOSTS` in settings to prevent calls to internal IPs (e.g., `169.254.169.254`).
*   [ ] **Audit Retention**: Configure a cron job to archive/delete `AuditLogEntry` rows older than X days if table size grows too large.

### 4. Observability
*   [ ] **Logs**: Configure the `JsonFormatter` to pipe structured logs to your ELK/Datadog stack.
*   [ ] **Trace IDs**: Ensure your load balancer passes `X-Trace-Id` headers so they propagate through the workflow.

## Scaling Patterns

### High Throughput Events
For high volume (1000+ events/sec):
1.  **Sharding**: Shard your `Outbox` table (requires custom engineering support atm).
2.  **Batching**: Configure triggers to batch events (e.g., process 100 webhook payloads in one workflow run) to reduce overhead.
3.  **Rule Indexing**: Ensure `RuleSpec.index_terms` matches your high-cardinality fields (`event.type`, `source_id`).

### LLM Cost Control
*   **Caching**: Enable caching in `LLMProvider` settings to avoid re-generating the same prompt.
*   **Budgets**: Set strict atomic budgets in `CostTracker` to prevent runaway bills.
